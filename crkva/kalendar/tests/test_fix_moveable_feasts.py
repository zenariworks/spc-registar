"""Tests for the ``fix_moveable_feasts`` command (issue #259).

The command must be idempotent and self-healing: convert one canonical row of
each Paschal-cycle feast to a moveable feast and prune leftover *fixed*
duplicates, repointing any household references first. Same-name feasts that
fall on *different* days (e.g. Св. Атанасије 31.1 vs 15.5) are legitimate and
must never be touched.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django_tenants.utils import schema_context

from kalendar.models import Slava
from registar.models import Domacinstvo, Osoba

EASTER_NAMES = [
    "Лазарева субота",
    "Улазак Господа Исуса Христа у Јерусалим",
    "Велики четвртак (Велико бденије)",
    "Велики петак",
    "Велика субота",
    "Васкрсење Господа исуса Христа",
    "Васкрски понедељак",
    "Васкрсни уторак",
    "Вазнесење Господње",
    "Силазак Светог Духа на апостоле-Педесетница-Тројице",
    "Духовски понедељак",
    "Духовски уторак",
]


class FixMoveableFeastsTests(TestCase):
    def setUp(self):
        # Чиста полазна тачка за ова имена у public шеми.
        with schema_context("public"):
            Slava.objects.filter(
                naziv__in=EASTER_NAMES + ["Свети Атанасије Велики"]
            ).delete()

    def _run(self):
        call_command("fix_moveable_feasts", stdout=StringIO(), stderr=StringIO())

    def test_converts_canonical_and_prunes_fixed_duplicate(self):
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
            self.assertIsNone(row.mesec)
            self.assertFalse(Slava.objects.filter(uid=dup.uid).exists())

    def test_reassigns_households_before_deleting_duplicate(self):
        with schema_context("public"):
            canonical = Slava.objects.create(naziv="Лазарева субота", pokretni=True)
            dup = Slava.objects.create(
                naziv="Лазарева субота", pokretni=False, dan=3, mesec=4
            )

        # Домаћинство (tenant) погрешно везано за вишак (фиксну копију).
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
        self._run()  # не сме да пукне нити да направи нове редове

        with schema_context("public"):
            self.assertEqual(
                Slava.objects.filter(naziv="Велики петак").count(), 1
            )

    def test_leaves_legitimate_same_name_different_day_pair_untouched(self):
        # Атанасије 31.1 и 15.5 нису у Васкршњем циклусу → команда их не дира.
        with schema_context("public"):
            a = Slava.objects.create(
                naziv="Свети Атанасије Велики", dan=31, mesec=1
            )
            b = Slava.objects.create(
                naziv="Свети Атанасије Велики", dan=15, mesec=5
            )

        self._run()

        with schema_context("public"):
            self.assertEqual(
                Slava.objects.filter(naziv="Свети Атанасије Велики").count(), 2
            )
            for s in (a, b):
                s.refresh_from_db()
                self.assertFalse(s.pokretni)
