"""Тестови за services.merge (спајање дупликата адреса).

Покрива merge_adrese (пресмеравање FK + брисање губитника + self-merge
гард), adresa_fanout и batch_adresa_fanout (празан улаз + груписање +
константан број упита). Issue #222 — services/merge.py био на 34%.
"""

# pylint: disable=missing-function-docstring

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from registar.models import Adresa, Domacinstvo, Osoba, Svestenik
from registar.services.merge import adresa_fanout, batch_adresa_fanout, merge_adrese


class MergeAdreseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.loser = Adresa.objects.create(ulica="Стара", broj="1", mesto="Београд")
        cls.winner = Adresa.objects.create(ulica="Нова", broj="2", mesto="Београд")
        # Два парохијана, једно домаћинство и један свештеник на губитнику.
        cls.o1 = Osoba.objects.create(ime="А", prezime="А", adresa=cls.loser)
        cls.o2 = Osoba.objects.create(ime="Б", prezime="Б", adresa=cls.loser)
        domacin = Osoba.objects.create(ime="Дом", prezime="Дом", adresa=cls.loser)
        cls.dom = Domacinstvo.objects.create(domacin=domacin, adresa=cls.loser)
        cls.sv = Svestenik.objects.create(
            ime="Поп", prezime="Попић", zvanje="јереј", adresa=cls.loser
        )

    def test_merge_repoints_all_fks_and_deletes_loser(self):
        moved = merge_adrese(self.loser, self.winner)
        self.assertEqual(moved, {"osoba": 3, "domacinstvo": 1, "svestenik": 1})
        # Губитник обрисан.
        self.assertFalse(Adresa.objects.filter(uid=self.loser.uid).exists())
        # Све везе сада показују на победника.
        self.assertEqual(Osoba.objects.filter(adresa=self.winner).count(), 3)
        self.assertEqual(Domacinstvo.objects.filter(adresa=self.winner).count(), 1)
        self.assertEqual(Svestenik.objects.filter(adresa=self.winner).count(), 1)

    def test_merge_into_self_raises(self):
        with self.assertRaises(ValueError):
            merge_adrese(self.loser, self.loser)
        # Ништа није обрисано.
        self.assertTrue(Adresa.objects.filter(uid=self.loser.uid).exists())


class FanoutTests(TestCase):
    def test_adresa_fanout_counts(self):
        a = Adresa.objects.create(ulica="Главна", broj="10", mesto="Ниш")
        Osoba.objects.create(ime="Х", prezime="Х", adresa=a)
        Osoba.objects.create(ime="Y", prezime="Y", adresa=a)
        self.assertEqual(
            adresa_fanout(a), {"osoba": 2, "domacinstvo": 0, "svestenik": 0}
        )

    def test_batch_fanout_empty_input(self):
        self.assertEqual(batch_adresa_fanout([]), {})

    def test_batch_fanout_groups_per_address(self):
        a1 = Adresa.objects.create(ulica="Прва", broj="1", mesto="Нови Сад")
        a2 = Adresa.objects.create(ulica="Друга", broj="2", mesto="Нови Сад")
        Osoba.objects.create(ime="П1", prezime="П", adresa=a1)
        Osoba.objects.create(ime="П2", prezime="П", adresa=a1)
        Svestenik.objects.create(ime="С", prezime="С", zvanje="јереј", adresa=a2)
        result = batch_adresa_fanout([a1, a2])
        self.assertEqual(result[a1.uid], {"osoba": 2, "domacinstvo": 0, "svestenik": 0})
        self.assertEqual(result[a2.uid], {"osoba": 0, "domacinstvo": 0, "svestenik": 1})

    def test_batch_fanout_query_count_does_not_grow_with_n(self):
        # Кључна особина: број упита је константан без обзира на број адреса
        # (3 GROUP BY-а; режијски SET search_path под django-tenants је исти).
        few = [
            Adresa.objects.create(ulica=f"А{i}", broj=str(i), mesto="Бг")
            for i in range(3)
        ]
        with CaptureQueriesContext(connection) as ctx_few:
            batch_adresa_fanout(few)

        many = few + [
            Adresa.objects.create(ulica=f"Б{i}", broj=str(i), mesto="Бг")
            for i in range(20)
        ]
        with CaptureQueriesContext(connection) as ctx_many:
            batch_adresa_fanout(many)

        self.assertEqual(len(ctx_many.captured_queries), len(ctx_few.captured_queries))
