"""Basic tests for the slava-households view (slava_view)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from kalendar.models import Slava
from registar.models import Adresa, Domacinstvo, Osoba

User = get_user_model()


class SlavaDomacinstvaViewTests(TestCase):
    """slava_view.slava_domacinstva — render + context partitioning."""

    @classmethod
    def setUpTestData(cls):
        cls.slava = Slava.objects.create(
            naziv="Тест слава",
            mesec=5,
            dan=15,
            pokretni=False,
        )

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)

    def test_renders_for_existing_slava(self):
        url = reverse("slava_detail", kwargs={"uid": self.slava.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Тест слава")

    def test_returns_404_for_missing_uid(self):
        url = reverse("slava_detail", kwargs={"uid": 999_999})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 404)

    def test_passes_count_in_context(self):
        url = reverse("slava_detail", kwargs={"uid": self.slava.uid})
        r = self.client.get(url)
        self.assertIn("count", r.context)
        self.assertEqual(r.context["count"], 0)

    def test_partitions_members_in_context(self):
        """Each household in the context should carry .zivi_clanovi +
        .preminuli_clanovi attrs set by the view."""
        url = reverse("slava_detail", kwargs={"uid": self.slava.uid})
        r = self.client.get(url)
        self.assertIn("domacinstva", r.context)
        for d in r.context["domacinstva"]:
            self.assertTrue(hasattr(d, "zivi_clanovi"))
            self.assertTrue(hasattr(d, "preminuli_clanovi"))


class SlavaDomacinstvaGroupingTests(TestCase):
    """Issue #18: report groups households by street and shows holy water."""

    @classmethod
    def setUpTestData(cls):
        cls.slava = Slava.objects.create(
            naziv="Тест слава 2", mesec=6, dan=10, pokretni=False
        )
        gl1 = Adresa.objects.create(ulica="Главна", broj="1")
        gl2 = Adresa.objects.create(ulica="Главна", broj="2")
        sp = Adresa.objects.create(ulica="Споредна", broj="5")
        Domacinstvo.objects.create(
            domacin=Osoba.objects.create(ime="Марко", prezime="Петровић", pol="М"),
            slava=cls.slava, adresa=gl1, slavska_vodica=True, vaskrsnja_vodica=False,
        )
        Domacinstvo.objects.create(
            domacin=Osoba.objects.create(ime="Јована", prezime="Аврамовић", pol="Ж"),
            slava=cls.slava, adresa=gl2, slavska_vodica=False, vaskrsnja_vodica=True,
        )
        Domacinstvo.objects.create(
            domacin=Osoba.objects.create(ime="Лука", prezime="Јовановић", pol="М"),
            slava=cls.slava, adresa=sp, slavska_vodica=True, vaskrsnja_vodica=True,
        )
        # No-address household lands in the trailing "Без улице" group.
        Domacinstvo.objects.create(
            domacin=Osoba.objects.create(ime="Ана", prezime="Николић", pol="Ж"),
            slava=cls.slava,
        )

    def setUp(self):
        self.user = User.objects.create_user(username="grouptester", password="x")
        self.client.force_login(self.user)
        self.url = reverse("slava_detail", kwargs={"uid": self.slava.uid})

    def test_context_groups_by_street(self):
        r = self.client.get(self.url)
        self.assertIn("grupe", r.context)
        ulice = [g["ulica"] for g in r.context["grupe"]]
        self.assertEqual(ulice, ["Главна", "Споредна", "Без улице"])
        sizes = {g["ulica"]: len(g["domacinstva"]) for g in r.context["grupe"]}
        self.assertEqual(sizes, {"Главна": 2, "Споредна": 1, "Без улице": 1})

    def test_street_header_rendered(self):
        r = self.client.get(self.url)
        self.assertContains(r, "spisak__group-head")
        self.assertContains(r, "Главна")
        self.assertContains(r, "Споредна")

    def test_holy_water_rendered_with_yes_no(self):
        r = self.client.get(self.url)
        self.assertContains(r, "stavka__vodica")
        self.assertContains(r, "Славска водица")
        self.assertContains(r, "Васкршња водица")
        body = r.content.decode("utf-8")
        self.assertIn("да", body)
        self.assertIn("не", body)

    def test_count_includes_all_households(self):
        r = self.client.get(self.url)
        self.assertEqual(r.context["count"], 4)
