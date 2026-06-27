"""#278: подножје преписа потписује издавалац (пријављени корисник),
а не свештеник који је обавио чин.

Покрива:
- ``get_izdavalac``: везан профil → потпис+парохија свештеника; фолбек на
  парохију тенанта + име корисника када профил није везан,
- рендеровање подножја крштенице/венчанице: подножје = издавалац, тело =
  свештеник који је обавио чин (издавалац ≠ обавио чин).
"""

# pylint: disable=missing-function-docstring

import datetime
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba, Svestenik, Vencanje
from registar.models.parohija import Parohija
from registar.services.izdavalac import get_izdavalac

User = get_user_model()


class GetIzdavalacTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parohija = Parohija.objects.create(naziv="Парохија Чукарица")
        cls.priest_user = User.objects.create_user(
            username="pop", password="x", first_name="Марко", last_name="Марковић"
        )
        cls.svestenik = Svestenik.objects.create(
            ime="Марко",
            prezime="Марковић",
            zvanje="јереј",
            parohija=cls.parohija,
            user=cls.priest_user,
        )
        cls.plain_user = User.objects.create_user(
            username="laik", password="x", first_name="Лаза", last_name="Лазић"
        )

    def _req(self, user, tenant=None):
        req = RequestFactory().get("/")
        req.user = user
        req.tenant = tenant
        return req

    def test_linked_user_returns_priest_signature_and_parish(self):
        data = get_izdavalac(self._req(self.priest_user))
        self.assertEqual(str(data["potpis"]), str(self.svestenik))
        self.assertEqual(data["parohija"], self.parohija)

    def test_unlinked_user_falls_back_to_tenant_naziv_and_full_name(self):
        tenant = SimpleNamespace(naziv="Парохија Земун")
        data = get_izdavalac(self._req(self.plain_user, tenant))
        self.assertEqual(data["parohija"], "Парохија Земун")
        self.assertEqual(data["potpis"], "Лаза Лазић")

    def test_unlinked_user_without_name_falls_back_to_username(self):
        u = User.objects.create_user(username="bezimena", password="x")
        data = get_izdavalac(self._req(u, None))
        self.assertEqual(data["potpis"], "bezimena")
        self.assertEqual(data["parohija"], "")


class _FooterBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.par_a = Parohija.objects.create(naziv="Парохија А")
        cls.par_b = Parohija.objects.create(naziv="Парохија Б")
        # свештеник који је обавио чин
        cls.performer = Svestenik.objects.create(
            ime="Ана", prezime="Анић", zvanje="протојереј", parohija=cls.par_a
        )
        # издавалац (пријављени корисник) са својим профилом/парохијом
        cls.issuer_user = User.objects.create_user(
            username="izdavalac", password="x", first_name="Бора", last_name="Борић"
        )
        cls.issuer = Svestenik.objects.create(
            ime="Бора",
            prezime="Борић",
            zvanje="јереј",
            parohija=cls.par_b,
            user=cls.issuer_user,
        )
        cls.hram = Hram.objects.create(naziv="Храм Свете Петке")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.issuer_user)


class KrstenjeFooterTests(_FooterBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.dete = Osoba.objects.create(ime="Лазар", prezime="Лазић", pol="М")
        cls.krstenje = Krstenje.objects.create(
            dete=cls.dete,
            hram=cls.hram,
            svestenik=cls.performer,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 2, 10),
        )

    def test_footer_shows_issuer_body_shows_performer(self):
        url = reverse("krstenje_detail", kwargs={"uid": self.krstenje.uid})
        html = self.client.get(url).content.decode()
        # подножје = издавалац (пријављени корисник) + његова парохија
        self.assertIn(
            '<div class="krst-field-footer_paroh">%s</div>' % self.issuer, html
        )
        self.assertIn(
            '<div class="krst-field-footer_parohija">%s</div>' % self.par_b, html
        )
        # тело и даље приказује свештеника који је обавио чин
        self.assertIn(
            '<div class="krst-table-field krst-field-svestenik">%s</div>'
            % self.performer,
            html,
        )
        # издавалац ≠ обавио чин: потпис није свештеник из записа
        self.assertNotIn(
            '<div class="krst-field-footer_paroh">%s</div>' % self.performer, html
        )


class VencanjeFooterTests(_FooterBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.zenik = Osoba.objects.create(ime="Урош", prezime="Урошевић", pol="М")
        cls.nevesta = Osoba.objects.create(ime="Тамара", prezime="Тамарић", pol="Ж")
        cls.vencanje = Vencanje.objects.create(
            zenik=cls.zenik,
            nevesta=cls.nevesta,
            hram=cls.hram,
            svestenik=cls.performer,
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 6, 6),
        )

    def test_footer_shows_issuer_body_shows_performer(self):
        url = reverse("vencanje_detail", kwargs={"uid": self.vencanje.uid})
        html = self.client.get(url).content.decode()
        self.assertIn(
            '<div class="venc-field-footer_paroh">%s</div>' % self.issuer, html
        )
        self.assertIn(
            '<div class="venc-field-footer_parohija">%s</div>' % self.par_b, html
        )
        self.assertIn(
            '<div class="venc-table-field venc-field-svestenik">%s</div>'
            % self.performer,
            html,
        )
        self.assertNotIn(
            '<div class="venc-field-footer_paroh">%s</div>' % self.performer, html
        )
