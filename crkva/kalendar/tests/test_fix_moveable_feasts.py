"""Tests for moveable Paschal-cycle feasts and the JSONL seed source (issue #259).

Covers the durable fix:

* ``crkva/fixtures/slave.jsonl`` is the single seed source — explicit per-feast
  fields, fixed and moveable together, no fixed copies of moveable feasts.
* ``kalendar.feasts`` is the canonical moveable definition; the JSONL stays in
  sync with it.
* ``unos_slava`` seeds from the JSONL idempotently (moveable as moveable).
* ``fix_moveable_feasts`` reconciles existing DBs (one moveable row, prunes
  fixed duplicates, repoints household refs first).

Same-name feasts on *different* days (e.g. Св. Атанасије 31.1 vs 15.5) are
legitimate and must never be touched.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

import io
import json
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
JSONL = os.path.join(settings.BASE_DIR, "fixtures", "slave.jsonl")
# 12 дана чији је покретни празник склоњен са фиксног датума и враћен фиксни светац.
RESTORED_DAYS = [(4, 3), (4, 4), (4, 8), (4, 9), (4, 10), (4, 11),
                 (4, 12), (4, 13), (5, 20), (5, 30), (5, 31), (6, 1)]


def _load_jsonl():
    return [json.loads(l) for l in io.open(JSONL, encoding="utf-8") if l.strip()]


def _purge_moveable():
    with schema_context("public"):
        Slava.objects.filter(
            naziv__in=list(MOVEABLE_FEAST_NAMES) + [LEGIT_SAME_NAME]
        ).delete()


class SlaveJsonlSourceTests(TestCase):
    """The JSONL seed file is well-formed and agrees with the canonical list."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rows = _load_jsonl()
        cls.fixed = [r for r in cls.rows if not r["pokretni"]]
        cls.moveable = [r for r in cls.rows if r["pokretni"]]

    def test_counts(self):
        self.assertEqual(len(self.moveable), len(MOVEABLE_FEASTS))
        self.assertEqual(len(self.fixed), 365)

    def test_fixed_have_dates_and_no_offset(self):
        for r in self.fixed:
            self.assertIsNotNone(r["dan"], r["naziv"])
            self.assertIsNotNone(r["mesec"], r["naziv"])
            self.assertIsNone(r["offset_dani"], r["naziv"])

    def test_moveable_have_offset_and_no_date(self):
        for r in self.moveable:
            self.assertIsNone(r["dan"], r["naziv"])
            self.assertIsNone(r["mesec"], r["naziv"])
            self.assertIsNotNone(r["offset_dani"], r["naziv"])

    def test_no_fixed_row_uses_a_moveable_name(self):
        fixed_names = {r["naziv"] for r in self.fixed}
        self.assertEqual(fixed_names & MOVEABLE_FEAST_NAMES, set())

    def test_moveable_rows_match_feasts_module(self):
        from_jsonl = {(r["naziv"], r["offset_dani"]) for r in self.moveable}
        from_code = {(f["naziv"], f["offset_dani"]) for f in MOVEABLE_FEASTS}
        self.assertEqual(from_jsonl, from_code)

    def test_restored_days_have_a_fixed_feast(self):
        bydate = {(r["mesec"], r["dan"]): r for r in self.fixed}
        for m, d in RESTORED_DAYS:
            self.assertIn((m, d), bydate, f"{d}.{m} missing a fixed feast")
            self.assertFalse(bydate[(m, d)]["pokretni"])

    def test_full_year_fixed_coverage(self):
        import calendar
        days = {(m, d) for m in range(1, 13)
                for d in range(1, calendar.monthrange(2025, m)[1] + 1)}
        covered = {(r["mesec"], r["dan"]) for r in self.fixed}
        # (28.2) је историјска празнина у изворним подацима, ван опсега #259.
        self.assertEqual(days - covered, {(2, 28)})


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

    def test_idempotent(self):
        upsert_moveable_feasts()
        upsert_moveable_feasts()
        with schema_context("public"):
            for feast in MOVEABLE_FEASTS:
                self.assertEqual(Slava.objects.filter(naziv=feast["naziv"]).count(), 1)


class UnosSlavaSeederTests(TestCase):
    def setUp(self):
        _purge_moveable()

    def test_seeds_moveable_as_moveable_and_no_fixed_copy(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for feast in MOVEABLE_FEASTS:
                rows = Slava.objects.filter(naziv=feast["naziv"])
                self.assertEqual(rows.count(), 1, feast["naziv"])
                self.assertTrue(rows.get().pokretni, feast["naziv"])
            self.assertFalse(
                Slava.objects.filter(
                    naziv__in=MOVEABLE_FEAST_NAMES, pokretni=False
                ).exists()
            )

    def test_restored_days_get_a_fixed_saint(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for m, d in RESTORED_DAYS:
                qs = Slava.objects.filter(mesec=m, dan=d, pokretni=False)
                self.assertTrue(qs.exists(), f"no fixed saint on {d}.{m}")

    def test_idempotent_no_duplicates(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for feast in MOVEABLE_FEASTS:
                self.assertEqual(
                    Slava.objects.filter(naziv=feast["naziv"]).count(), 1, feast["naziv"]
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
                naziv="Васкрсење Господа исуса Христа", pokretni=False, dan=11, mesec=4
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
