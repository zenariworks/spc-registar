"""Тестови за KrstenjeFilter и VencanjeFilter (FilterSet претрага).

Ови FilterSet-ови су били неупотребљени и поломљени (референцирали су
@property имена и сирова FK поља уместо релационих путања), па су падали
са FieldError при сваком термину. Овде се потврђује исправљена претрага:
по имену (ћир/лат), по датуму, и AND семантика више термина.
Issue #222 — filters/*_filter.py били на 55% (filter_search неизвршен).
"""

# pylint: disable=missing-function-docstring

import datetime

from django.test import TestCase
from registar.filters import KrstenjeFilter, VencanjeFilter
from registar.models import Hram, Krstenje, Osoba, Vencanje


class KrstenjeFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dete = Osoba.objects.create(ime="Марко", prezime="Марковић", pol="М")
        cls.otac = Osoba.objects.create(ime="Петар", prezime="Марковић", pol="М")
        cls.majka = Osoba.objects.create(ime="Ана", prezime="Марковић", pol="Ж")
        cls.kum = Osoba.objects.create(ime="Лазар", prezime="Кумовић", pol="М")
        cls.hram = Hram.objects.create(naziv="Храм")
        cls.krstenje = Krstenje.objects.create(
            dete=cls.dete, otac=cls.otac, majka=cls.majka, kum=cls.kum,
            knjiga=1, broj=1, strana=1, redni_broj=1, godina_registracije=2024,
            datum=datetime.date(2024, 5, 17),
            vanbracno=False, blizanac=False, telesna_mana=False, hram=cls.hram,
        )
        # Несродан запис да се потврди да филтер заиста сужава.
        other = Osoba.objects.create(ime="Никола", prezime="Илић", pol="М")
        Krstenje.objects.create(
            dete=other, knjiga=1, broj=2, strana=1, redni_broj=2,
            godina_registracije=2024, datum=datetime.date(2020, 1, 1),
            vanbracno=False, blizanac=False, telesna_mana=False, hram=cls.hram,
        )

    def _search(self, term):
        return list(
            KrstenjeFilter(
                data={"search": term}, queryset=Krstenje.objects.all()
            ).qs
        )

    def test_search_by_child_name(self):
        self.assertEqual(self._search("Марко"), [self.krstenje])

    def test_search_by_father_surname(self):
        # И отац и дете и мајка деле презиме Марковић → тачно овај запис.
        self.assertEqual(self._search("Марковић"), [self.krstenje])

    def test_search_by_kum(self):
        self.assertEqual(self._search("Кумовић"), [self.krstenje])

    def test_search_latin_finds_cyrillic(self):
        self.assertEqual(self._search("Marko"), [self.krstenje])

    def test_search_by_date_string(self):
        self.assertEqual(self._search("2024-05-17"), [self.krstenje])

    def test_multi_term_and_semantics(self):
        self.assertEqual(self._search("Марко Лазар"), [self.krstenje])

    def test_no_match_returns_empty(self):
        self.assertEqual(self._search("Непостојеће"), [])


class VencanjeFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.zenik = Osoba.objects.create(ime="Душан", prezime="Зекић", pol="М")
        cls.nevesta = Osoba.objects.create(ime="Јелена", prezime="Нинић", pol="Ж")
        cls.kum = Osoba.objects.create(ime="Огњен", prezime="Кумић", pol="М")
        cls.stari_svat = Osoba.objects.create(ime="Вук", prezime="Сватић", pol="М")
        cls.hram = Hram.objects.create(naziv="Саборна црква")
        cls.vencanje = Vencanje.objects.create(
            zenik=cls.zenik, nevesta=cls.nevesta, kum=cls.kum,
            stari_svat=cls.stari_svat, hram=cls.hram,
            datum=datetime.date(2023, 9, 3),
        )
        z2 = Osoba.objects.create(ime="Иван", prezime="Иванић", pol="М")
        n2 = Osoba.objects.create(ime="Маја", prezime="Мајић", pol="Ж")
        Vencanje.objects.create(
            zenik=z2, nevesta=n2, datum=datetime.date(2019, 2, 2)
        )

    def _search(self, term):
        return list(
            VencanjeFilter(
                data={"search": term}, queryset=Vencanje.objects.all()
            ).qs
        )

    def test_search_by_groom(self):
        self.assertEqual(self._search("Душан"), [self.vencanje])

    def test_search_by_bride(self):
        self.assertEqual(self._search("Јелена"), [self.vencanje])

    def test_search_by_kum(self):
        self.assertEqual(self._search("Кумић"), [self.vencanje])

    def test_search_by_stari_svat(self):
        self.assertEqual(self._search("Сватић"), [self.vencanje])

    def test_search_by_hram(self):
        self.assertEqual(self._search("Саборна"), [self.vencanje])

    def test_search_latin_finds_cyrillic(self):
        self.assertEqual(self._search("Dusan"), [self.vencanje])

    def test_search_by_date_string(self):
        self.assertEqual(self._search("2023-09-03"), [self.vencanje])

    def test_no_match_returns_empty(self):
        self.assertEqual(self._search("Непостојеће"), [])
