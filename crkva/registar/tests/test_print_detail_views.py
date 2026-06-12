"""#222: покривеност за PDF приказе и детаљ/измена приказе.

`krstenje_view`, `vencanje_view` и `svestenik_view` били су на 66% јер PDF
генерисање, детаљни приказ свештеника и поједине izmena гране нису биле
извршаване ниједним тестом. Овај модул покрива:

- KrstenjePDF / VencanjePDF / SvestenikPDF — приказ генерише HTML из
  pdf шаблона и прослеђује га WeasyPrint-у; сам PDF-енџин је mock-ован
  (његова native зависност pydyf пуца у чистом CI окружењу, а и није
  предмет теста — тестирамо логику приказа: get_object, контекст са
  историјским снимцима особа и састављање HTTP одговора),
- PrikazSvestenika — контекст детаља (историја + повезана крштења/венчања),
- izmena_krstenja / izmena_vencanja — POST → save → redirect грана,
- izmena_svestenika — GET форме за измену.
"""

# pylint: disable=missing-function-docstring

import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba, Svestenik, Vencanje
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()

FAKE_PDF = b"%PDF-1.4 (test stub)"


class _PdfBase(TestCase):
    """Заједнички setup: суперкорисник (read view-ови нису role-gated)."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="pdf-admin", email="a@a.test", password="x"
        )
        cls.hram = Hram.objects.create(naziv="Храм Свете Петке")
        cls.svestenik = Svestenik.objects.create(
            ime="Сава", prezime="Савић", zvanje="јереј"
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def _get_pdf(self, html_target, url, prefix):
        """GET PDF приказа уз mock-ован WeasyPrint HTML.write_pdf()."""
        with patch(html_target) as mock_html:
            mock_html.return_value.write_pdf.return_value = FAKE_PDF
            response = self.client.get(url)
        # Приказ је заиста позвао WeasyPrint са израђеним HTML стрингом.
        self.assertTrue(mock_html.called)
        _, kwargs = mock_html.call_args
        self.assertIn("string", kwargs)
        self.assertTrue(kwargs["string"])
        self.assertEqual(response.status_code, 200, msg=response.content[:400])
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response.content, FAKE_PDF)
        self.assertIn(f"filename={prefix}-", response["Content-Disposition"])
        return response


class KrstenjePDFTests(_PdfBase):
    """KrstenjePDF: контекст + историјски снимци dete/otac/majka (kum=None)."""

    TARGET = "registar.views.krstenje_view.HTML"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.dete = Osoba.objects.create(ime="Лазар", prezime="Лазић", pol="М")
        cls.otac = Osoba.objects.create(ime="Петар", prezime="Лазић", pol="М")
        cls.majka = Osoba.objects.create(ime="Марија", prezime="Лазић", pol="Ж")
        # kum остаје None → покрива `else: context[...] = None` грану.
        cls.krstenje = Krstenje.objects.create(
            dete=cls.dete,
            otac=cls.otac,
            majka=cls.majka,
            hram=cls.hram,
            svestenik=cls.svestenik,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 2, 10),
        )

    def test_pdf_renders(self):
        # datum (2024) претходи историјском снимку (created сада) → as_of
        # баца DoesNotExist → покрива except грану у снимку особе.
        self._get_pdf(
            self.TARGET,
            reverse("krstenje_pdf", kwargs={"uid": self.krstenje.uid}),
            "krstenje",
        )

    def test_pdf_without_datum_falls_back_to_created(self):
        # datum=None → event_date пада на created → as_of враћа снимак особе
        # → покрива успешну грану доделе историјског снимка.
        k = Krstenje.objects.create(
            dete=self.dete,
            hram=self.hram,
            svestenik=self.svestenik,
            godina_registracije=2025,
            redni_broj=1,
            knjiga=2,
            strana=1,
            broj=1,
            datum=None,
        )
        self._get_pdf(
            self.TARGET,
            reverse("krstenje_pdf", kwargs={"uid": k.uid}),
            "krstenje",
        )


class VencanjePDFTests(_PdfBase):
    """VencanjePDF: контекст + историјски снимци ženik/nevesta."""

    TARGET = "registar.views.vencanje_view.HTML"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.zenik = Osoba.objects.create(ime="Урош", prezime="Урошевић", pol="М")
        cls.nevesta = Osoba.objects.create(ime="Тамара", prezime="Тамарић", pol="Ж")
        cls.vencanje = Vencanje.objects.create(
            zenik=cls.zenik,
            nevesta=cls.nevesta,
            hram=cls.hram,
            svestenik=cls.svestenik,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 6),
        )

    def test_pdf_renders(self):
        self._get_pdf(
            self.TARGET,
            reverse("vencanje_pdf", kwargs={"uid": self.vencanje.uid}),
            "vencanje",
        )

    def test_pdf_without_datum_falls_back_to_created(self):
        v = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            hram=self.hram,
            svestenik=self.svestenik,
            godina_registracije=2025,
            redni_broj=1,
            knjiga=2,
            strana=1,
            broj=1,
            datum=None,
        )
        self._get_pdf(
            self.TARGET,
            reverse("vencanje_pdf", kwargs={"uid": v.uid}),
            "vencanje",
        )


class SvestenikPDFTests(_PdfBase):
    """SvestenikPDF: генерисање PDF документа свештеника."""

    def test_pdf_renders(self):
        self._get_pdf(
            "registar.views.svestenik_view.HTML",
            reverse("svestenik_pdf", kwargs={"uid": self.svestenik.uid}),
            "svestenik",
        )


class PrikazSvestenikaDetailTests(_PdfBase):
    """Детаљ свештеника: контекст укључује повезана крштења и венчања."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        dete = Osoba.objects.create(ime="Дете", prezime="Детић", pol="М")
        cls.krstenje = Krstenje.objects.create(
            dete=dete,
            hram=cls.hram,
            svestenik=cls.svestenik,
            godina_registracije=2024,
            redni_broj=2,
            knjiga=1,
            strana=1,
            broj=2,
            datum=datetime.date(2024, 3, 1),
        )
        z = Osoba.objects.create(ime="Жен", prezime="Женић", pol="М")
        n = Osoba.objects.create(ime="Нев", prezime="Невић", pol="Ж")
        cls.vencanje = Vencanje.objects.create(
            zenik=z,
            nevesta=n,
            hram=cls.hram,
            svestenik=cls.svestenik,
            godina_registracije=2024,
            redni_broj=3,
            knjiga=1,
            strana=1,
            broj=3,
            datum=datetime.date(2024, 4, 1),
        )

    def test_detail_renders_with_related_counts(self):
        r = self.client.get(
            reverse("svestenik_detail", kwargs={"uid": self.svestenik.uid})
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["krstenja_count"], 1)
        self.assertEqual(r.context["vencanja_count"], 1)
        self.assertIn(self.krstenje, list(r.context["krstenja"]))
        self.assertIn(self.vencanje, list(r.context["vencanja"]))


class IzmenaSaveBranchTests(TestCase):
    """izmena_* POST→save→redirect и GET гране које недостају у покривености."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc-222", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.priest = User.objects.create_user(username="svest-222", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.hram = Hram.objects.create(naziv="Храм")
        cls.svestenik = Svestenik.objects.create(
            ime="Сава", prezime="Савић", zvanje="јереј"
        )
        cls.dete = Osoba.objects.create(ime="Лазар", prezime="Лазић", pol="М")
        cls.otac = Osoba.objects.create(ime="Петар", prezime="Лазић", pol="М")
        cls.majka = Osoba.objects.create(ime="Марија", prezime="Лазић", pol="Ж")
        cls.kum = Osoba.objects.create(ime="Кум", prezime="Кумић", pol="М")
        cls.zenik = Osoba.objects.create(ime="Урош", prezime="Урошевић", pol="М")
        cls.nevesta = Osoba.objects.create(ime="Тамара", prezime="Тамарић", pol="Ж")

    def setUp(self):
        self.client = Client()

    def test_izmena_krstenja_post_saves_and_redirects(self):
        k = Krstenje.objects.create(
            dete=self.dete,
            otac=self.otac,
            majka=self.majka,
            hram=self.hram,
            svestenik=self.svestenik,
            godina_registracije=2024,
            redni_broj=10,
            knjiga=1,
            strana=1,
            broj=10,
            datum=datetime.date(2024, 2, 10),
        )
        self.client.force_login(self.clerk)
        payload = {
            "redni_broj": "10",
            "godina_registracije": "2024",
            "knjiga": "1",
            "strana": "1",
            "broj": "10",
            "datum": "2024-02-10",
            "vreme": "11:30",
            "hram": str(self.hram.pk),
            "dete": str(self.dete.pk),
            "otac": str(self.otac.pk),
            "majka": str(self.majka.pk),
            "kum": str(self.kum.pk),
            "svestenik": str(self.svestenik.pk),
            "po_redu": "1",
            "ime_blizanca": "",
            "mesto_registracije": "Београд",
            "datum_registracije": "2024-02-12",
            "maticni_broj": "12345",
            "strana_registracije": "7",
            "primedba": "измењено",
        }
        r = self.client.post(reverse("izmena_krstenja", kwargs={"uid": k.uid}), payload)
        self.assertEqual(r.status_code, 302, msg=r.content[:600])
        self.assertEqual(
            r["Location"],
            reverse("krstenje_detail", kwargs={"uid": k.uid}),
        )
        k.refresh_from_db()
        self.assertEqual(k.primedba, "измењено")

    def test_izmena_vencanja_post_saves_and_redirects(self):
        v = Vencanje.objects.create(
            zenik=self.zenik,
            nevesta=self.nevesta,
            hram=self.hram,
            svestenik=self.svestenik,
            godina_registracije=2024,
            redni_broj=11,
            knjiga=1,
            strana=1,
            broj=11,
            datum=datetime.date(2024, 6, 1),
            razresenje=False,
        )
        self.client.force_login(self.clerk)
        payload = {
            "zenik": str(self.zenik.pk),
            "nevesta": str(self.nevesta.pk),
            "kum": str(self.kum.pk),
            "godina_registracije": "2024",
            "redni_broj": "11",
            "knjiga": "1",
            "strana": "1",
            "broj": "11",
            "datum": "2024-06-01",
            "zenik_rb_brak": "1",
            "nevesta_rb_brak": "1",
            "hram": str(self.hram.pk),
            "svestenik": str(self.svestenik.pk),
            "razresenje": "on",
        }
        r = self.client.post(reverse("izmena_vencanja", kwargs={"uid": v.uid}), payload)
        self.assertEqual(r.status_code, 302, msg=r.content[:600])
        self.assertEqual(
            r["Location"],
            reverse("vencanje_detail", kwargs={"uid": v.uid}),
        )
        v.refresh_from_db()
        self.assertTrue(v.razresenje)

    def test_izmena_svestenika_get_renders_edit_form(self):
        self.client.force_login(self.priest)
        r = self.client.get(
            reverse("izmena_svestenika", kwargs={"uid": self.svestenik.uid})
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["is_edit"])
        self.assertEqual(r.context["svestenik"], self.svestenik)


class VencanjeDetailRenderTests(TestCase):
    """Детаљни (HTML) приказ венчања — регресије садржаја (#16)."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="venc-detail", email="vd@a.test", password="x"
        )
        cls.hram = Hram.objects.create(naziv="Храм Свете Петке")
        cls.svestenik = Svestenik.objects.create(
            ime="Сава", prezime="Савић", zvanje="јереј"
        )
        cls.zenik = Osoba.objects.create(ime="Урош", prezime="Урошевић", pol="М")
        cls.nevesta = Osoba.objects.create(ime="Тамара", prezime="Тамарић", pol="Ж")
        # adresa_zenika остаје None → mesto_hram би имао водећи зарез без заштите
        cls.vencanje = Vencanje.objects.create(
            zenik=cls.zenik,
            nevesta=cls.nevesta,
            hram=cls.hram,
            svestenik=cls.svestenik,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 6),
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def test_mesto_hram_nema_vodeci_zarez(self):
        response = self.client.get(
            reverse("vencanje_detail", kwargs={"uid": self.vencanje.uid})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'venc-field-mesto_hram">, ')

    def test_opis_zenika_spaja_bez_praznih_delova(self):
        # зеник има само име/презиме → нема празних делова ни зареза на крају
        self.assertEqual(self.vencanje.opis_zenika, "Урош Урошевић")

    def test_vera_i_narodnost_mala_slova(self):
        # вера/народност су заједничке именице → мала слова (Православна→православна)
        self.assertEqual(Vencanje._mala("Православна"), "православна")
        self.assertEqual(Vencanje._mala("Српска"), "српска")
        self.assertEqual(Vencanje._mala(None), "")

    def test_prazni_roditelji_ne_prave_prazne_redove(self):
        # родитељи нису постављени → празни описи и без празних <span> редова
        self.assertEqual(self.vencanje.opis_svekra, "")
        self.assertEqual(self.vencanje.opis_svekrve, "")
        response = self.client.get(
            reverse("vencanje_detail", kwargs={"uid": self.vencanje.uid})
        )
        # оба родитеља празна → ћелија приказује цртицу „-" (празна ћелија)
        self.assertContains(
            response,
            '<div class="venc-table-field venc-field-roditelji_zenika">'
            "<span>-</span></div>",
        )

    def test_prazne_celije_prikazuju_crticu(self):
        # без датума/места рођења и без сведока → ћелије приказују „-", не „None"
        response = self.client.get(
            reverse("vencanje_detail", kwargs={"uid": self.vencanje.uid})
        )
        self.assertContains(
            response,
            '<div class="venc-table-field venc-field-rodjenje_zenika">'
            "<span>-</span></div>",
        )
        self.assertContains(
            response,
            '<div class="venc-table-field venc-field-svedoci"><span>-</span></div>',
        )
