"""load_data --from dbf-* фасада: рутирање и валидација (без стварног увоза).

Фасада повезује load_dbf + importuj_dbf под шемом закупца. Овде се тестира
само гранање и провере — стварни DBF увоз захтева staging податке.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class LoadDataDbfFacadeTests(TestCase):
    def _run(self, *args):
        call_command("load_data", *args, stdout=StringIO(), stderr=StringIO())

    def test_dbf_requires_tenant(self):
        with self.assertRaises(CommandError):
            self._run("--from", "dbf-zip:/tmp/x.zip")

    def test_dbf_missing_path_rejected(self):
        with self.assertRaises(CommandError):
            self._run("--from", "dbf-zip:", "--tenant", "test_tenant")

    def test_dbf_nonexistent_source_rejected(self):
        with self.assertRaises(CommandError):
            self._run(
                "--from", "dbf-zip:/nema/ovakve/putanje.zip", "--tenant", "test_tenant"
            )

    def test_fixture_not_implemented(self):
        with self.assertRaises(CommandError):
            self._run("--from", "fixture:/tmp/x.json", "--tenant", "test_tenant")

    def test_unknown_source_rejected(self):
        with self.assertRaises(CommandError):
            self._run("--from", "bogus", "--tenant", "test_tenant")

    def test_mock_dry_run_lists_steps(self):
        out = StringIO()
        call_command(
            "load_data",
            "--from",
            "mock",
            "--tenant",
            "test_tenant",
            "--dry-run",
            stdout=out,
        )
        ispis = out.getvalue()
        self.assertIn("unos_sifarnika", ispis)
        self.assertIn("unos_svestenika", ispis)
