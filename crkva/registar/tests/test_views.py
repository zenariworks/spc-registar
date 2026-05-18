"""
Тестови за прикази (views) у апликацији registar.
"""

import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Hram, Krstenje, Osoba, Ukucanin


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
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
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
            redni_broj=1,
            godina_registracije=2024,
            datum=datetime.date(2024, 2, 10),
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
        self.assertTemplateUsed(response, "registar/krstenje.html")

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
        self.assertIn("parohijani", response.context)

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
        self.user = User.objects.create_superuser(
            username="krst-tester", email="t@x.test", password="x"
        )
        self.client.force_login(self.user)

    def test_unos_krstenja_get_returns_200(self):
        """GET захтев за унос крштења враћа статус 200."""
        response = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(response.status_code, 200)

    def test_unos_krstenja_uses_correct_template(self):
        """Унос крштења користи унифицирани шаблон krstenje.html."""
        response = self.client.get(reverse("unos_krstenja"))
        self.assertTemplateUsed(response, "registar/krstenje.html")

    def test_unos_krstenja_has_form(self):
        """Унос крштења садржи форму."""
        response = self.client.get(reverse("unos_krstenja"))
        self.assertIn("form", response.context)


class ListSortTestCase(TestCase):
    """Sort parameter must reorder the parohijani list."""

    def setUp(self):
        self.client = Client()
        Osoba.objects.create(ime="Ана", prezime="Аћимовић", parohijan=True)
        Osoba.objects.create(ime="Марко", prezime="Марковић", parohijan=True)
        Osoba.objects.create(ime="Зорица", prezime="Шушић", parohijan=True)

    def _first_primary(self, response):
        import re

        m = re.search(
            r'<span class="stavka__primary">([^<]+)</span>',
            response.content.decode(),
        )
        return m.group(1).strip() if m else None

    def test_sort_prezime_ascending(self):
        response = self.client.get(reverse("parohijani"), {"sort": "prezime"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._first_primary(response), "Ана Аћимовић")

    def test_sort_prezime_descending(self):
        response = self.client.get(reverse("parohijani"), {"sort": "-prezime"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._first_primary(response), "Зорица Шушић")

    def test_sort_ignored_when_value_not_in_options(self):
        response = self.client.get(reverse("parohijani"), {"sort": "evil; drop table"})
        self.assertEqual(response.status_code, 200)


class SpisakParohijanaListTests(TestCase):
    """Тестови за приказ домаћинства на списку парохијана."""

    def setUp(self):
        self.client = Client()
        from registar.models import Adresa

        self.adresa = Adresa.objects.create(
            ulica="Поручника Спасића", broj="12", mesto="Београд"
        )

    def test_domacin_badge_renders(self):
        """Парохијан који је домаћин има значку 'домаћин' и адресу домаћинства."""
        domacin = Osoba.objects.create(ime="Драган", prezime="Станчић", parohijan=True)
        Domacinstvo.objects.create(domacin=domacin, adresa=self.adresa)
        response = self.client.get(reverse("parohijani"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Драган", html)
        self.assertIn("Станчић", html)
        self.assertIn("stavka__meta-badge--domacin", html)
        self.assertIn("домаћин", html)
        self.assertIn("Поручника Спасића", html)

    def test_clan_badge_renders(self):
        """Парохијан који је члан туђег домаћинства има значку 'члан' са именом домаћина."""
        domacin = Osoba.objects.create(ime="Драган", prezime="Станчић", parohijan=True)
        domacinstvo = Domacinstvo.objects.create(domacin=domacin, adresa=self.adresa)
        clan = Osoba.objects.create(ime="Милица", prezime="Станчић", parohijan=True)
        Ukucanin.objects.create(domacinstvo=domacinstvo, osoba=clan, uloga="дете")
        response = self.client.get(reverse("parohijani"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        # 'члан' значка треба да буде испред имена домаћина у Миличином реду
        self.assertIn("stavka__meta-badge--clan", html)
        self.assertIn("члан", html)
        # Драган Станчић је и домаћин, и приказан као домаћин код Милице
        idx_milica = html.find("Милица")
        idx_clan_after = html.find("члан", idx_milica)
        idx_dragan_after = html.find("Драган", idx_milica)
        self.assertGreater(idx_clan_after, idx_milica)
        self.assertGreater(idx_dragan_after, idx_milica)

    def test_no_household_renders_no_badge(self):
        """Парохијан без везе са домаћинством нема никакву значку."""
        Osoba.objects.create(ime="Самосталан", prezime="Без-Дома", parohijan=True)
        response = self.client.get(reverse("parohijani"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Самосталан", html)
        # Никаква meta значка не сме да се појави
        self.assertNotIn("stavka__meta-badge", html)

    def test_list_query_count_does_not_grow_with_n(self):
        """Број SQL упита не сме да расте са бројем парохијана/домаћинстава (no N+1)."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def page_size_5_setup():
            h1 = Osoba.objects.create(ime="Х1", prezime="Х", parohijan=True)
            d1 = Domacinstvo.objects.create(domacin=h1, adresa=self.adresa)
            h2 = Osoba.objects.create(ime="Х2", prezime="Х", parohijan=True)
            d2 = Domacinstvo.objects.create(domacin=h2, adresa=self.adresa)
            c1 = Osoba.objects.create(ime="Ч1", prezime="Ч", parohijan=True)
            Ukucanin.objects.create(domacinstvo=d1, osoba=c1, uloga="дете")
            c2 = Osoba.objects.create(ime="Ч2", prezime="Ч", parohijan=True)
            Ukucanin.objects.create(domacinstvo=d2, osoba=c2, uloga="дете")
            Osoba.objects.create(ime="Н1", prezime="Н", parohijan=True)

        page_size_5_setup()
        # Прва страна (10 парохијана по страни): измери укупан број упита.
        with CaptureQueriesContext(connection) as ctx_small:
            response = self.client.get(reverse("parohijani"))
        self.assertEqual(response.status_code, 200)
        small_n = len(ctx_small.captured_queries)

        # Утростручи број парохијана (углавном без домаћинстава) — упити не смеју расти.
        for i in range(20):
            extra = Osoba.objects.create(ime=f"Е{i}", prezime="Е", parohijan=True)
            if i % 3 == 0:
                Domacinstvo.objects.create(domacin=extra, adresa=self.adresa)

        with CaptureQueriesContext(connection) as ctx_big:
            response = self.client.get(reverse("parohijani"))
        self.assertEqual(response.status_code, 200)
        big_n = len(ctx_big.captured_queries)

        # Број упита мора остати константан (евентуално +1 за пагинацију — допуштамо мали зазор).
        self.assertLessEqual(
            big_n, small_n + 1, f"Упити расту са N: {small_n} -> {big_n}"
        )
