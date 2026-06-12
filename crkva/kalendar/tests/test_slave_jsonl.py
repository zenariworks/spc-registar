"""Tests for the JSONL slava seed source and the moveable-feast calculation.

After issue #259 the calendar has a single source of truth:

* ``crkva/fixtures/slave.jsonl`` — every feast (fixed and moveable) with
  explicit fields; moveable feasts carry ``offset_dani`` and no date.
* ``unos_slava`` seeds it idempotently.
* ``Slava.get_datum`` / ``calc_vaskrs`` compute moveable dates from Pascha.

No separate moveable-feast module or conversion command is needed: the JSONL
holds the data, the model holds the math.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

import calendar
import datetime
import io
import json
import os
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django_tenants.utils import schema_context
from kalendar.models import Slava

JSONL = os.path.join(settings.BASE_DIR, "fixtures", "slave.jsonl")
RESTORED_DAYS = [
    (4, 3),
    (4, 4),
    (4, 8),
    (4, 9),
    (4, 10),
    (4, 11),
    (4, 12),
    (4, 13),
    (5, 20),
    (5, 30),
    (5, 31),
    (6, 1),
]


def _load_jsonl():
    return [
        json.loads(line) for line in io.open(JSONL, encoding="utf-8") if line.strip()
    ]


def _moveable_names(rows):
    return {r["naziv"] for r in rows if r["pokretni"]}


def _purge(names):
    with schema_context("public"):
        Slava.objects.filter(naziv__in=list(names)).delete()


class SlaveJsonlSourceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rows = _load_jsonl()
        cls.fixed = [r for r in cls.rows if not r["pokretni"]]
        cls.moveable = [r for r in cls.rows if r["pokretni"]]

    def test_counts(self):
        self.assertEqual(len(self.fixed), 365)
        self.assertEqual(len(self.moveable), 12)

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

    def test_no_name_is_both_fixed_and_moveable(self):
        fixed_names = {r["naziv"] for r in self.fixed}
        self.assertEqual(fixed_names & _moveable_names(self.rows), set())

    def test_restored_days_have_a_fixed_feast(self):
        bydate = {(r["mesec"], r["dan"]): r for r in self.fixed}
        for m, d in RESTORED_DAYS:
            self.assertIn((m, d), bydate, f"{d}.{m} missing a fixed feast")

    def test_full_year_fixed_coverage(self):
        days = {
            (m, d)
            for m in range(1, 13)
            for d in range(1, calendar.monthrange(2025, m)[1] + 1)
        }
        covered = {(r["mesec"], r["dan"]) for r in self.fixed}
        # (28.2) је историјска празнина у изворним подацима, ван опсега #259.
        self.assertEqual(days - covered, {(2, 28)})


class UnosSlavaSeederTests(TestCase):
    def setUp(self):
        self.rows = _load_jsonl()
        self.moveable_names = _moveable_names(self.rows)
        _purge(self.moveable_names)

    def test_seeds_moveable_as_moveable_no_fixed_copy(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for name in self.moveable_names:
                rows = Slava.objects.filter(naziv=name)
                self.assertEqual(rows.count(), 1, name)
                self.assertTrue(rows.get().pokretni, name)
            self.assertFalse(
                Slava.objects.filter(
                    naziv__in=self.moveable_names, pokretni=False
                ).exists()
            )

    def test_restored_days_get_a_fixed_saint(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for m, d in RESTORED_DAYS:
                self.assertTrue(
                    Slava.objects.filter(mesec=m, dan=d, pokretni=False).exists(),
                    f"no fixed saint on {d}.{m}",
                )

    def test_idempotent_no_duplicates(self):
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        call_command("unos_slava", stdout=StringIO(), stderr=StringIO())
        with schema_context("public"):
            for name in self.moveable_names:
                self.assertEqual(Slava.objects.filter(naziv=name).count(), 1, name)


class SlavaCalcTests(SimpleTestCase):
    """Дате покретних празника рачуна модел (offset од Васкрса)."""

    def test_pascha_offset_zero_equals_vaskrs(self):
        s = Slava(naziv="Васкрс", pokretni=True, offset_dani=0, offset_nedelje=0)
        self.assertEqual(s.get_datum(2025), Slava.calc_vaskrs(2025))

    def test_offset_shifts_from_vaskrs(self):
        vaskrs = Slava.calc_vaskrs(2025)
        s = Slava(
            naziv="Духовски уторак", pokretni=True, offset_dani=51, offset_nedelje=0
        )
        self.assertEqual(s.get_datum(2025), vaskrs + datetime.timedelta(days=51))

    def test_fixed_feast_uses_date(self):
        s = Slava(naziv="Никољдан", pokretni=False, dan=19, mesec=12)
        self.assertEqual(s.get_datum(2025), datetime.date(2025, 12, 19))
