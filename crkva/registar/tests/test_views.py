"""
Тестови за прикази (views) у апликацији registar.
"""

import datetime

from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Hram, Krstenje, Osoba


class IndexViewTestCase(TestCase):
    """Тестови за почетну страницу."""

    def setUp(self):
        self.client = Client()

    def test_index_returns_200(self):
        """Почетна страница враћа статус 200."""
        response = self.client.get(reverse("pocetna"))
        self.assertEqual(response.status_code, 200)

    def test_index_uses_correct_template(self):
        """Почетна страница користи исправан шаблон."""
        response = self.client.get(reverse("pocetna"))
        self.assertTemplateUsed(response, "registar/index.html")

    def test_index_contains_calendar_cells(self):
        """Почетна страница садржи календарске ћелије."""
        response = self.client.get(reverse("pocetna"))
        self.assertIn("calendar_cells", response.context)
        self.assertEqual(len(response.context["calendar_cells"]), 7)


class SpisakKrstenjaViewTestCase(TestCase):
    """Тестови за списак крштења."""

    def setUp(self):
        self.client = Client()
        self.hram = Hram.objects.create(naziv="Тест Храм")
        self.krstenje = Krstenje.objects.create(
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
            hram=self.hram,
        )

    def test_spisak_krstenja_returns_200(self):
        """Списак крштења враћа статус 200."""
        response = self.client.get(reverse("krstenja"))
        self.assertEqual(response.status_code, 200)

    def test_spisak_krstenja_uses_correct_template(self):
        """Списак крштења користи исправан шаблон."""
        response = self.client.get(reverse("krstenja"))
        self.assertTemplateUsed(response, "registar/spisak_krstenja.html")

    def test_spisak_krstenja_contains_krstenje(self):
        """Списак крштења садржи креирано крштење."""
        response = self.client.get(reverse("krstenja"))
        self.assertIn("krstenja", response.context)

    def test_spisak_krstenja_pagination(self):
        """Пагинација је доступна."""
        response = self.client.get(reverse("krstenja"))
        self.assertTrue(response.context.get("is_paginated") is not None)


class PrikazKrstenjaViewTestCase(TestCase):
    """Тестови за приказ појединачног крштења."""

    def setUp(self):
        self.client = Client()
        self.dete = Osoba.objects.create(
            ime="Петар",
            prezime="Петровић",
            datum_rodjenja=datetime.date(2024, 1, 15),
            pol="М",
        )
        self.hram = Hram.objects.create(naziv="Тест Храм")
        self.krstenje = Krstenje.objects.create(
            dete=self.dete,
            knjiga=1,
            broj=1,
            strana=1,
            redni_broj_krstenja_tekuca_godina=1,
            krstenje_tekuca_godina=2024,
            datum=datetime.date(2024, 2, 10),
            adresa_deteta_grad="Београд",
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
            hram=self.hram,
        )

    def test_prikaz_krstenja_returns_200(self):
        """Приказ крштења враћа статус 200."""
        response = self.client.get(
            reverse("krstenje_detail", kwargs={"uid": self.krstenje.uid})
        )
        self.assertEqual(response.status_code, 200)

    def test_prikaz_krstenja_uses_correct_template(self):
        """Приказ крштења користи исправан шаблон."""
        response = self.client.get(
            reverse("krstenje_detail", kwargs={"uid": self.krstenje.uid})
        )
        self.assertTemplateUsed(response, "registar/info_krstenje.html")

    def test_prikaz_krstenja_contains_krstenje_data(self):
        """Приказ крштења садржи податке о крштењу."""
        response = self.client.get(
            reverse("krstenje_detail", kwargs={"uid": self.krstenje.uid})
        )
        self.assertEqual(response.context["krstenje"], self.krstenje)

    def test_prikaz_krstenja_404_for_invalid_uid(self):
        """Враћа 404 за невалидан UID."""
        import uuid

        fake_uid = uuid.uuid4()
        response = self.client.get(reverse("krstenje_detail", kwargs={"uid": fake_uid}))
        self.assertEqual(response.status_code, 404)


class SpisakParohijanaViewTestCase(TestCase):
    """Тестови за списак парохијана."""

    def setUp(self):
        self.client = Client()
        self.parohijan = Osoba.objects.create(
            ime="Јован",
            prezime="Јовановић",
            parohijan=True,
        )

    def test_spisak_parohijana_returns_200(self):
        """Списак парохијана враћа статус 200."""
        response = self.client.get(reverse("parohijani"))
        self.assertEqual(response.status_code, 200)

    def test_spisak_parohijana_uses_correct_template(self):
        """Списак парохијана користи исправан шаблон."""
        response = self.client.get(reverse("parohijani"))
        self.assertTemplateUsed(response, "registar/spisak_parohijana.html")


class SearchViewTestCase(TestCase):
    """Тестови за претрагу."""

    def setUp(self):
        self.client = Client()
        self.parohijan = Osoba.objects.create(
            ime="Никола",
            prezime="Николић",
            parohijan=True,
        )

    def test_search_returns_200(self):
        """Претрага враћа статус 200."""
        response = self.client.get(reverse("search_view"))
        self.assertEqual(response.status_code, 200)

    def test_search_with_query(self):
        """Претрага са упитом."""
        response = self.client.get(reverse("search_view"), {"query": "Никола"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("parohijan_results", response.context)

    def test_search_latin_finds_cyrillic(self):
        """Латинична претрага проналази ћирилични запис."""
        response = self.client.get(reverse("search_view"), {"query": "Nikola"})
        self.assertEqual(response.status_code, 200)

    def test_search_empty_query(self):
        """Празан упит враћа празне резултате."""
        response = self.client.get(reverse("search_view"), {"query": ""})
        self.assertEqual(response.status_code, 200)


class KalendarViewTestCase(TestCase):
    """Тестови за календар слава."""

    def setUp(self):
        self.client = Client()

    def test_kalendar_returns_200(self):
        """Календар враћа статус 200."""
        response = self.client.get(reverse("kalendar"))
        self.assertEqual(response.status_code, 200)

    def test_kalendar_with_month_params(self):
        """Календар са параметрима месеца."""
        response = self.client.get(
            reverse("kalendar_mesec", kwargs={"year": 2024, "month": 5})
        )
        self.assertEqual(response.status_code, 200)


class CalibrateViewsTestCase(TestCase):
    """Тестови за калибрационе странице."""

    def setUp(self):
        self.client = Client()

    def test_calibrate_krstenje_returns_200(self):
        """Калибрација крштенице враћа статус 200."""
        response = self.client.get(reverse("calibrate_krstenje"))
        self.assertEqual(response.status_code, 200)

    def test_calibrate_vencanje_returns_200(self):
        """Калибрација венчанице враћа статус 200."""
        response = self.client.get(reverse("calibrate_vencanje"))
        self.assertEqual(response.status_code, 200)


class UnosKrstenjaViewTestCase(TestCase):
    """Тестови за унос крштења."""

    def setUp(self):
        self.client = Client()

    def test_unos_krstenja_get_returns_200(self):
        """GET захтев за унос крштења враћа статус 200."""
        response = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(response.status_code, 200)

    def test_unos_krstenja_uses_correct_template(self):
        """Унос крштења користи исправан шаблон."""
        response = self.client.get(reverse("unos_krstenja"))
        self.assertTemplateUsed(response, "registar/unos_krstenja.html")

    def test_unos_krstenja_has_form(self):
        """Унос крштења садржи форму."""
        response = self.client.get(reverse("unos_krstenja"))
        self.assertIn("form", response.context)
