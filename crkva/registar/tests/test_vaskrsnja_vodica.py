"""Tests for the Easter-water (васкршња водица) feature (#26, #27, #325).

Since #325 the standalone per-street report is gone: the `vaskrsnja_vodica`
URL redirects to the unified Vaskrs slava page, which lists households flagged
`vaskrsnja_vodica=True`, resolved by the selected priest`s parish. This module
also keeps the parish-scoped household-list + print coverage (#26).
"""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from kalendar.models import Slava
from registar.models import Adresa, Domacinstvo, Osoba, Parohija, Svestenik

User = get_user_model()


class VaskrsnjaVodicaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Vaskrs: movable feast with zero offset (the anchor) — #325.
        cls.vaskrs = Slava.objects.create(
            naziv="Васкрсење Господа Исуса Христа",
            opsti_naziv="Васкрс",
            pokretni=True,
            offset_dani=0,
            offset_nedelje=0,
        )

        cls.p3 = Parohija.objects.create(naziv="3")
        cls.p9 = Parohija.objects.create(naziv="9")

        # Two priests in parish 3 (priests rotate; parish is the stable unit).
        cls.sv_old = Svestenik.objects.create(
            ime="Милан", prezime="Старији", zvanje="јереј", parohija=cls.p3
        )
        cls.sv_new = Svestenik.objects.create(
            ime="Ново", prezime="Млађи", zvanje="јереј", parohija=cls.p3
        )
        # A priest in another parish, and one with no parish.
        cls.sv_other = Svestenik.objects.create(
            ime="Друг", prezime="Деветка", zvanje="јереј", parohija=cls.p9
        )
        cls.sv_noparish = Svestenik.objects.create(
            ime="Без", prezime="Парохије", zvanje="јереј", parohija=None
        )

        # Streets assigned to the OLD priest of parish 3.
        a_glavna = Adresa.objects.create(ulica="Главна", broj="1", svestenik=cls.sv_old)
        a_sporedna = Adresa.objects.create(
            ulica="Споредна", broj="2", svestenik=cls.sv_old
        )
        a_other = Adresa.objects.create(ulica="Друга", broj="3", svestenik=cls.sv_other)

        def hh(ime, adresa, vodica):
            o = Osoba.objects.create(ime=ime, prezime="Тест", pol="М")
            return Domacinstvo.objects.create(
                domacin=o, adresa=adresa, vaskrsnja_vodica=vodica
            )

        hh("Аца", a_glavna, True)
        hh("Бора", a_sporedna, True)
        hh("Вера", a_glavna, False)  # not Easter-water → excluded
        hh("Гога", a_other, True)  # other parish

    def setUp(self):
        self.user = User.objects.create_user(username="vodicauser", password="x")
        self.client.force_login(self.user)

    # ---- redirect to the unified Vaskrs slava page (#325) ----

    def test_report_url_redirects_to_vaskrs_slava(self):
        target = reverse("slava_detail", kwargs={"uid": self.vaskrs.uid})
        r = self.client.get(reverse("vaskrsnja_vodica"))
        self.assertRedirects(r, target, fetch_redirect_response=False)

    def test_report_url_preserves_svestenik_param(self):
        target = reverse("slava_detail", kwargs={"uid": self.vaskrs.uid})
        r = self.client.get(reverse("vaskrsnja_vodica"), {"svestenik": self.sv_new.pk})
        self.assertRedirects(
            r, f"{target}?svestenik={self.sv_new.pk}", fetch_redirect_response=False
        )

    # ---- the unified page lists Easter-water households by parish ----

    def url(self, sv=None):
        u = reverse("slava_detail", kwargs={"uid": self.vaskrs.uid})
        return f"{u}?svestenik={sv}" if sv is not None else u

    def test_unified_page_lists_only_easter_water(self):
        # No filter → every vaskrsnja_vodica=True household (Аца, Бора, Гога),
        # never "Вера" (vodica=False) nor krsna-slava rows.
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["count"], 3)
        self.assertTrue(r.context["je_vaskrs"])

    def test_unified_page_resolves_by_parish_not_priest(self):
        # New parish-3 priest (no streets of his own) still sees parish-3
        # Easter-water households (Аца, Бора).
        r = self.client.get(self.url(self.sv_new.pk))
        self.assertEqual(r.context["count"], 2)

    def test_unified_page_other_parish_isolated(self):
        r = self.client.get(self.url(self.sv_other.pk))
        self.assertEqual(r.context["count"], 1)

    def test_unified_page_priest_without_parish(self):
        r = self.client.get(self.url(self.sv_noparish.pk))
        self.assertEqual(r.context["count"], 0)
        self.assertTrue(r.context["nema_parohije"])

    # ---- household list filter (domacinstva view, parish-scoped) ----

    def test_household_filter_by_parish_counts_all(self):
        # Filter is by parish and includes ALL households (not only vodica):
        # parish 3 has 3 households (Аца, Бора, Вера).
        r = self.client.get(reverse("domacinstva") + f"?svestenik={self.sv_new.pk}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["paginator"].count, 3)
        self.assertContains(r, "dom-svestenik-form")

    def test_household_filter_other_parish(self):
        r = self.client.get(reverse("domacinstva") + f"?svestenik={self.sv_other.pk}")
        self.assertEqual(r.context["paginator"].count, 1)

    def test_household_filter_priest_without_parish_empty(self):
        r = self.client.get(
            reverse("domacinstva") + f"?svestenik={self.sv_noparish.pk}"
        )
        self.assertEqual(r.context["paginator"].count, 0)

    # ---- print ----

    def test_print_grouped_by_street(self):
        r = self.client.get(
            reverse("domacinstva_print") + f"?svestenik={self.sv_new.pk}"
        )
        self.assertEqual(r.status_code, 200)
        ulice = [g["ulica"] for g in r.context["grupe"]]
        self.assertEqual(ulice, ["Главна", "Споредна"])
        self.assertEqual(r.context["ukupno"], 3)
