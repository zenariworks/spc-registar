"""Tests for moveable Paschal-cycle feasts (issue #259).

Covers the durable fix:

* ``kalendar.feasts`` is the single source of truth (``upsert_moveable_feasts``).
* The seed source ``fixtures/slave.sql`` no longer lists moveable feasts as
  fixed rows.
* Seeder ``unos_slava`` creates them as moveable, never as fixed, idempotently.
* ``fix_moveable_feasts`` reconciles existing DBs: ensures one moveable row and
  prunes fixed duplicates, repointing household refs first.

Same-name feasts on *different* days (e.g. Св. Атанасије 31.1 vs 15.5) are
legitimate and must never be touched.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

import io
import os
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django_tenants.utils import schema_context

from kalendar.feasts import (
    MOVEABLE_FEAST_NAMES,
    MOVEABLE_FEASTS,
    upsert_moveable_feasts,
)
from kalendar.models import Slava
from registar.models import Domacinstvo, Osoba

LEGIT_SAME_NAME = "Свети Атанасије Велики"


def _purge_moveable():
    with schema_context("public"):
        Slava.objects.filter(
            naziv__in=list(MOVEABLE_FEAST_NAMES) + [LEGIT_SAME_NAME]
        ).delete()


class MoveableFeastSourceTests(TestCase):
    """The canonical list and the seed file must agree (no fixed moveable rows)."""

    def test_slave_sql_lists_no_moveable_feast(self):
        # fixtures/slave.sql је релативно у односу на manage.py (crkva/).
        path = os.path.join(settings.BASE_DIR, "fixtures", "slave.sql")
        names = {
            line.strip().split(";")[0]
            for line in io.open(path, encoding="utf-8")
            if line.strip()
        }
        leaked = names & MOVEABLE_FEAST_NAMES
        self.assertEqual(
            leaked, set(), f"slave.sql still lists moveable feasts as fixed: {leaked}"
        )

    def test_every_moveable_feast_name_is_unique_in_list(self):
        self.assertEqual(len(MOVEABLE_FEAST_NAMES), len(MOVEABLE_FEASTS))


class UpsertMoveableFeastsTests(TestCase):
    def setUp(self):
        _purge_moveable()

    def test_creates_each_feast_as_single_moveable_row(self):
        upsert_moveable_feasts()
        with schema_context("public"):
            for feast in MOVEABLE_FEASTS:
                rows = Slava.objects.filter(naziv=feast["naziv"])
                self.assertEqual(rows.count(), 1, feast["naziv"])
                row = rows.get()
                self.assertTrue(row.pokretni)
                self.assertEqual(row.offset_dani, feast["offset_dani"])
                self.assertIsNone(row.dan)
                self.assertIsNone(row.mesec)

    def test_converts_existing_fixed_row_in_place(self):
        with schema_context("public"):
            fixed = Slava.objects.create(
                naziv="Васкрсење Господа исуса Христа",
                pokretni=False,
                dan=11,
                mesec=4,
            )
        upsert_moveable_feasts()
        with schema_context("public"):
            row = Slava.objects.get(naziv="Васкрсење Господа исуса Христа")
            self.assertEqual(row.uid, fixed.uid)  # исти ред, не нови
            self.assertTrue(row.pokretni)
            self.assertIsNone(row.dan)

    def test_idempotent(self):
        upsert_moveable_feasts()
        upsert_moveable_feasts()
        with schema_context("public"):
            for feast in MOVEABLE_FEASTS:
                self.assertEqual(
                    Slava.objects.filter(naziv=feast["naziv"]).count(), 1
                )


class UnosSlavaSeederTests(TestCase):
    def setUp(self):
        _purge_moveable()

    def test_unos_slava_creates_moveable_not_fixed(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for feast in MOVEABLE_FEASTS:
                rows = Slava.objects.filter(naziv=feast["naziv"])
                self.assertEqual(rows.count(), 1, feast["naziv"])
                self.assertTrue(rows.get().pokretni, feast["naziv"])
            # ниједан фиксни ред са именом покретног празника
            self.assertFalse(
                Slava.objects.filter(
                    naziv__in=MOVEABLE_FEAST_NAMES, pokretni=False
                ).exists()
            )

    def test_unos_slava_twice_makes_no_duplicates(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for feast in MOVEABLE_FEASTS:
                self.assertEqual(
                    Slava.objects.filter(naziv=feast["naziv"]).count(),
                    1,
                    feast["naziv"],
                )


class FixMoveableFeastsTests(TestCase):
    def setUp(self):
        _purge_moveable()

    def _run(self):
        call_command("fix_moveable_feasts", stdout=StringIO(), stderr=StringIO())

    def test_prunes_fixed_duplicate_and_keeps_moveable(self):
        with schema_context("public"):
            canonical = Slava.objects.create(
                naziv="Васкрсење Господа исуса Христа", pokretni=True
            )
            dup = Slava.objects.create(
                naziv="Васкрсење Господа исуса Христа",
                pokretni=False,
                dan=11,
                mesec=4,
            )
        self._run()
        with schema_context("public"):
            remaining = Slava.objects.filter(naziv="Васкрсење Господа исуса Христа")
            self.assertEqual(remaining.count(), 1)
            row = remaining.get()
            self.assertEqual(row.uid, canonical.uid)
            self.assertTrue(row.pokretni)
            self.assertEqual(row.offset_dani, 0)
            self.assertIsNone(row.dan)
            self.assertFalse(Slava.objects.filter(uid=dup.uid).exists())

    def test_creates_missing_feast(self):
        # Празан почетак → команда сама креира покретни ред.
        self._run()
        with schema_context("public"):
            row = Slava.objects.get(naziv="Духовски уторак")
            self.assertTrue(row.pokretni)
            self.assertEqual(row.offset_dani, 51)

    def test_reassigns_households_before_deleting_duplicate(self):
        with schema_context("public"):
            canonical = Slava.objects.create(naziv="Лазарева субота", pokretni=True)
            dup = Slava.objects.create(
                naziv="Лазарева субота", pokretni=False, dan=3, mesec=4
            )
        osoba = Osoba.objects.create(ime="Лазар", prezime="Лазић", pol="М")
        dom = Domacinstvo.objects.create(domacin=osoba, slava_id=dup.uid)

        self._run()

        dom.refresh_from_db()
        self.assertEqual(dom.slava_id, canonical.uid)
        with schema_context("public"):
            self.assertFalse(Slava.objects.filter(uid=dup.uid).exists())

    def test_idempotent_second_run_is_noop(self):
        with schema_context("public"):
            Slava.objects.create(naziv="Велики петак", pokretni=False, dan=9, mesec=4)
            Slava.objects.create(naziv="Велики петак", pokretni=False, dan=9, mesec=4)
        self._run()
        self._run()
        with schema_context("public"):
            self.assertEqual(Slava.objects.filter(naziv="Велики петак").count(), 1)

    def test_leaves_legitimate_same_name_different_day_pair_untouched(self):
        with schema_context("public"):
            a = Slava.objects.create(naziv=LEGIT_SAME_NAME, dan=31, mesec=1)
            b = Slava.objects.create(naziv=LEGIT_SAME_NAME, dan=15, mesec=5)
        self._run()
        with schema_context("public"):
            self.assertEqual(Slava.objects.filter(naziv=LEGIT_SAME_NAME).count(), 2)
            for s in (a, b):
                s.refresh_from_db()
                self.assertFalse(s.pokretni)
