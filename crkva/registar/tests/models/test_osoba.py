"""
Тестови за моделе у апликацији registar.
"""

import datetime

from django.test import TestCase
from registar.models import Narodnost, Osoba, Veroispovest


class OsobaModelTestCase(TestCase):
    """Тестови за модел Osoba."""

    def test_create_osoba(self):
        """Креирање особе са основним подацима."""
        osoba = Osoba.objects.create(
            ime="Никола",
            prezime="Петровић",
        )
        self.assertEqual(osoba.ime, "Никола")
        self.assertEqual(osoba.prezime, "Петровић")
        self.assertIsNotNone(osoba.uid)

    def test_str_representation(self):
        """Стринг репрезентација особе."""
        osoba = Osoba.objects.create(ime="Марко", prezime="Марковић")
        self.assertEqual(str(osoba), "Марко Марковић")

    def test_parohijan_default_false(self):
        """Подразумевана вредност за парохијана је False."""
        osoba = Osoba.objects.create(ime="Петар", prezime="Петровић")
        self.assertFalse(osoba.parohijan)

    def test_osoba_with_full_data(self):
        """Креирање особе са свим подацима."""
        vera = Veroispovest.objects.create(naziv="Православна")
        narod = Narodnost.objects.create(naziv="Српска")
        osoba = Osoba.objects.create(
            ime="Јован",
            prezime="Јовановић",
            devojacko_prezime=None,
            parohijan=True,
            mesto_rodjenja="Београд",
            datum_rodjenja=datetime.date(1990, 5, 15),
            vreme_rodjenja=datetime.time(10, 30),
            pol="М",
            zanimanje=None,
            veroispovest=vera,
            narodnost=narod,
        )
        self.assertEqual(osoba.pol, "М")
        self.assertEqual(osoba.datum_rodjenja, datetime.date(1990, 5, 15))
        self.assertTrue(osoba.parohijan)
        self.assertEqual(str(osoba.veroispovest), "Православна")
        self.assertEqual(str(osoba.narodnost), "Српска")

    def test_pol_choices(self):
        """Пол може бити само М или Ж."""
        osoba_m = Osoba.objects.create(ime="Петар", prezime="Петровић", pol="М")
        osoba_z = Osoba.objects.create(ime="Марија", prezime="Марковић", pol="Ж")
        self.assertEqual(osoba_m.pol, "М")
        self.assertEqual(osoba_z.pol, "Ж")

    def test_timestamps_auto_created(self):
        """Временске ознаке се аутоматски креирају."""
        osoba = Osoba.objects.create(ime="Тест", prezime="Тестић")
        self.assertIsNotNone(osoba.created)
        self.assertIsNotNone(osoba.modified)
