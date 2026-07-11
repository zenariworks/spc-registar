"""#340: seed_svestenici обједињује mock и dummy изворе.

Некадашња ``unos_svestenika`` (dummy placeholder свештеници) спојена је у
``seed_svestenici`` као ``--from dummy``; ``--from mock`` остаје реалистичан
подразумевани извор. ``migracija_svestenika`` (DBF миграција) остаје засебно.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from registar.models import Svestenik


class SeedSvesteniciTests(TestCase):
    def _seed(self, **kwargs):
        args = ["--tenant", "test_tenant", "--seed", "1"]
        for key, value in kwargs.items():
            args += [f"--{key}", str(value)]
        call_command("seed_svestenici", *args, stdout=StringIO())

    def test_dummy_source_creates_rows(self):
        self._seed(**{"from": "dummy", "count": 3})
        self.assertEqual(Svestenik.objects.count(), 3)

    def test_mock_source_creates_rows(self):
        self._seed(**{"from": "mock", "count": 3})
        self.assertEqual(Svestenik.objects.count(), 3)

    def test_unknown_source_rejected(self):
        with self.assertRaises((CommandError, SystemExit)):
            call_command(
                "seed_svestenici",
                "--tenant",
                "test_tenant",
                "--from",
                "bogus",
                stdout=StringIO(),
            )

    def test_reset_clears_before_seeding(self):
        self._seed(**{"from": "dummy", "count": 2})
        call_command(
            "seed_svestenici",
            "--tenant",
            "test_tenant",
            "--from",
            "dummy",
            "--count",
            "2",
            "--reset",
            stdout=StringIO(),
        )
        self.assertEqual(Svestenik.objects.count(), 2)
