"""#340: групне typer подкоманде (seed/migracija) диспечују на relocated класе."""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from registar.models import Narodnost, Svestenik


class SeedGroupTests(TestCase):
    def test_seed_svestenici_creates_rows(self):
        call_command(
            "seed",
            "svestenici",
            "--tenant",
            "test_tenant",
            "--count",
            "2",
            "--seed",
            "1",
            stdout=StringIO(),
        )
        self.assertEqual(Svestenik.objects.count(), 2)

    def test_seed_sifarnika_seeds_lookups(self):
        call_command("seed", "sifarnika", "--tenant", "test_tenant", stdout=StringIO())
        self.assertGreater(Narodnost.objects.count(), 0)
