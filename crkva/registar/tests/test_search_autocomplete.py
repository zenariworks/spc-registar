"""Тестови за search_autocomplete JSON endpoint (груписани предлози).

Покрива кратак упит (< 2 знака → празно), и груписане резултате по типу
ентитета (парохијани, свештеници, крштења, венчања) са рангирањем.
Issue #222 — views/search_view.py био на 51% (autocomplete неизвршен).
"""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba, Svestenik, Vencanje

User = get_user_model()


class SearchAutocompleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="auto", email="a@a.test", password="x"
        )
        cls.parohijan = Osoba.objects.create(
            ime="Стефан",
            prezime="Стефановић",
            pol="М",
            datum_rodjenja=datetime.date(1990, 1, 1),
        )
        cls.svestenik = Svestenik.objects.create(
            ime="Сава", prezime="Савић", zvanje="јереј"
        )
        cls.hram = Hram.objects.create(naziv="Храм")
        dete = Osoba.objects.create(ime="Михаило", prezime="Михаиловић", pol="М")
        cls.krstenje = Krstenje.objects.create(
            dete=dete,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 1, 2),
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
            hram=cls.hram,
        )
        zenik = Osoba.objects.create(ime="Урош", prezime="Урошевић", pol="М")
        nevesta = Osoba.objects.create(ime="Тамара", prezime="Тамарић", pol="Ж")
        cls.vencanje = Vencanje.objects.create(
            zenik=zenik,
            nevesta=nevesta,
            hram=cls.hram,
            datum=datetime.date(2023, 6, 6),
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _labels(self, term):
        r = self.client.get(reverse("search_autocomplete"), {"q": term})
        self.assertEqual(r.status_code, 200)
        return r.json(), [g["label"] for g in r.json()["groups"]]

    def test_short_query_returns_empty(self):
        r = self.client.get(reverse("search_autocomplete"), {"q": "С"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"groups": []})

    def test_parohijan_group(self):
        data, labels = self._labels("Стефан")
        self.assertIn("Парохијани", labels)
        grupa = next(g for g in data["groups"] if g["label"] == "Парохијани")
        self.assertEqual(grupa["items"][0]["text"], "Стефан Стефановић")

    def test_svestenik_group(self):
        _, labels = self._labels("Савић")
        self.assertIn("Свештеници", labels)

    def test_krstenje_group(self):
        _, labels = self._labels("Михаило")
        self.assertIn("Крштења", labels)

    def test_vencanje_group(self):
        _, labels = self._labels("Урош")
        self.assertIn("Венчања", labels)

    def test_latin_query_finds_cyrillic(self):
        _, labels = self._labels("Stefan")
        self.assertIn("Парохијани", labels)
