"""Tests for the Easter-water priest territory feature (#26).

Covers: the per-street report (resolved by parish, not by individual priest),
and the household-list filter + print scoped to a priest's parish.
"""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from registar.models import Adresa, Domacinstvo, Osoba, Parohija, Svestenik

User = get_user_model()


class VaskrsnjaVodicaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        a_other = Adresa.objects.create(
            ulica="Друга", broj="3", svestenik=cls.sv_other
        )

        def hh(ime, adresa, vodica):
            o = Osoba.objects.create(ime=ime, prezime="Тест", pol="М")
            return Domacinstvo.objects.create(
                domacin=o, adresa=adresa, vaskrsnja_vodica=vodica
            )

        hh("Аца", a_glavna, True)
        hh("Бора", a_sporedna, True)
        hh("Вера", a_glavna, False)  # not Easter-water → excluded from report
        hh("Гога", a_other, True)  # other parish

    def setUp(self):
        self.user = User.objects.create_user(username="vodicauser", password="x")
        self.client.force_login(self.user)

    # ---- report ----

    def url(self, sv=None):
        u = reverse("vaskrsnja_vodica")
        return f"{u}?svestenik={sv}" if sv is not None else u

    def test_report_resolves_by_parish_not_priest(self):
        # Picking the NEW parish-3 priest (no streets directly assigned to him)
        # must still show parish-3 streets (assigned to the old priest).
        r = self.client.get(self.url(self.sv_new.pk))
        self.assertEqual(r.status_code, 200)
        ulice = {row["ulica"]: row["broj"] for row in r.context["redovi"]}
        self.assertEqual(ulice, {"Главна": 1, "Споредна": 1})  # vodica-only counts
        self.assertEqual(r.context["ukupno"], 2)

    def test_report_excludes_non_easter_water(self):
        r = self.client.get(self.url(self.sv_old.pk))
        ulice = {row["ulica"]: row["broj"] for row in r.context["redovi"]}
        self.assertEqual(ulice.get("Главна"), 1)  # "Вера" (vodica=False) not counted

    def test_report_other_parish_isolated(self):
        r = self.client.get(self.url(self.sv_other.pk))
        ulice = {row["ulica"]: row["broj"] for row in r.context["redovi"]}
        self.assertEqual(ulice, {"Друга": 1})

    def test_report_priest_without_parish(self):
        r = self.client.get(self.url(self.sv_noparish.pk))
        self.assertTrue(r.context["nema_parohije"])
        self.assertEqual(r.context["redovi"], [])

    def test_report_no_selection_prompts(self):
        r = self.client.get(self.url())
        self.assertIsNone(r.context["svestenik"])
        self.assertEqual(r.context["redovi"], [])

    # ---- household list filter ----

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
