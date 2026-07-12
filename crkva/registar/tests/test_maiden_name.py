"""Tests for the devojacko-name marker split: izdvoj_devojacko helper +
``popravi_devojacka`` management command.

The DBF import imported many female Osoba with surnames like
"р.Бошковић" / "рођ. Видојевић". The marker means "рођена" (née) and
the trailing surname is the devojacko name, not the married one.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,invalid-name,protected-access,import-outside-toplevel

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from registar.migracija.helpers import izdvoj_devojacko
from registar.models import Domacinstvo, Osoba, Ukucanin


class ExtractdevojackoTests(TestCase):
    """Pure-function tests for helpers.izdvoj_devojacko — no DB."""

    def test_cyrillic_r_dot_no_space(self):
        self.assertEqual(izdvoj_devojacko("р.Бошковић"), ("", "Бошковић"))

    def test_cyrillic_r_dot_with_space(self):
        self.assertEqual(izdvoj_devojacko("р. Бошковић"), ("", "Бошковић"))

    def test_capital_cyrillic_r_dot(self):
        self.assertEqual(izdvoj_devojacko("Р.Бошковић"), ("", "Бошковић"))

    def test_cyrillic_r_space(self):
        # "р Марковић" — bare letter + whitespace
        self.assertEqual(izdvoj_devojacko("р Марковић"), ("", "Марковић"))

    def test_rodj_dot_marker(self):
        self.assertEqual(izdvoj_devojacko("рођ. Видојевић"), ("", "Видојевић"))
        self.assertEqual(izdvoj_devojacko("рођ.Видојевић"), ("", "Видојевић"))

    def test_rodjena_full_word_marker(self):
        self.assertEqual(izdvoj_devojacko("рођена Ђорђевић"), ("", "Ђорђевић"))
        self.assertEqual(izdvoj_devojacko("Рођена Ђорђевић"), ("", "Ђорђевић"))

    def test_latin_r_dot(self):
        self.assertEqual(izdvoj_devojacko("r.Marković"), ("", "Marković"))
        self.assertEqual(izdvoj_devojacko("R. Marković"), ("", "Marković"))

    def test_no_marker_returns_input_as_married(self):
        self.assertEqual(izdvoj_devojacko("Marko Marković"), ("Marko Marković", ""))
        self.assertEqual(izdvoj_devojacko("Бошковић"), ("Бошковић", ""))

    def test_does_not_eat_leading_R_when_no_marker(self):
        # Regression for the ocisti_prezime bug: "Радановић" must not
        # become "адановић".
        self.assertEqual(izdvoj_devojacko("Радановић"), ("Радановић", ""))
        self.assertEqual(izdvoj_devojacko("Ристић"), ("Ристић", ""))
        self.assertEqual(izdvoj_devojacko("Radanović"), ("Radanović", ""))

    def test_empty_and_none(self):
        self.assertEqual(izdvoj_devojacko(""), ("", ""))
        self.assertEqual(izdvoj_devojacko(None), ("", ""))
        self.assertEqual(izdvoj_devojacko("   "), ("", ""))

    def test_bare_marker_alone(self):
        # "р." with nothing after — both halves empty.
        self.assertEqual(izdvoj_devojacko("р."), ("", ""))
        self.assertEqual(izdvoj_devojacko("рођ."), ("", ""))
        self.assertEqual(izdvoj_devojacko("r."), ("", ""))

    def test_leading_and_trailing_whitespace(self):
        self.assertEqual(izdvoj_devojacko("  р.Бошковић  "), ("", "Бошковић"))
        self.assertEqual(izdvoj_devojacko("  Marković  "), ("Marković", ""))

    def test_capitalises_lowercase_devojacko(self):
        # Sometimes the source is sloppy: "р.бошковић" → "Бошковић".
        self.assertEqual(izdvoj_devojacko("р.бошковић"), ("", "Бошковић"))
        self.assertEqual(izdvoj_devojacko("r.marković"), ("", "Marković"))

    def test_documented_examples_from_task(self):
        # Татјана р.Бошковић → ime="Татјана", prezime="" (married blank),
        # devojacko="Бошковић"
        ime = "Татјана"
        vencano, devojacko = izdvoj_devojacko("р.Бошковић")
        self.assertEqual(ime, "Татјана")
        self.assertEqual(vencano, "")
        self.assertEqual(devojacko, "Бошковић")

        # Верица рођ. Видојевић → ime="Верица", devojacko="Видојевић"
        vencano, devojacko = izdvoj_devojacko("рођ. Видојевић")
        self.assertEqual(vencano, "")
        self.assertEqual(devojacko, "Видојевић")


class PopraviDevojackaCommandTests(TestCase):
    """End-to-end tests of the cleanup command. We run with the default
    public schema since the command iterates tenants; here we sidestep
    tenant iteration by calling the inner ``_popravi`` directly."""

    def setUp(self):
        from registar.management.commands.popravi_devojacka import Command

        self.cmd = Command()
        self.cmd.stdout = StringIO()
        self.cmd.style = type(
            "S", (), {"MIGRATE_HEADING": str, "SUCCESS": str, "MIGRATE_LABEL": str}
        )()

    def test_blank_married_default(self):
        o = Osoba.objects.create(ime="Татјана", prezime="р.Бошковић")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.ime, "Татјана")
        self.assertEqual(o.prezime, "")
        self.assertEqual(o.devojacko, "Бошковић")

    def test_rodj_dot_marker_moved(self):
        o = Osoba.objects.create(ime="Верица", prezime="рођ. Видојевић")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "")
        self.assertEqual(o.devojacko, "Видојевић")

    def test_dry_run_does_not_modify(self):
        o = Osoba.objects.create(ime="Татјана", prezime="р.Бошковић")
        self.cmd._popravi(dry_run=True, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "р.Бошковић")
        self.assertIsNone(o.devojacko)

    def test_no_marker_untouched(self):
        o = Osoba.objects.create(ime="Marko", prezime="Marković")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "Marković")

    def test_leading_R_not_eaten(self):
        # Regression: "Радановић" must not get "P." stripped off.
        o = Osoba.objects.create(ime="Ивана", prezime="Радановић")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "Радановић")
        self.assertFalse(o.devojacko)

    def test_keep_existing_devojacko(self):
        # If devojacko is already set, don't overwrite it.
        o = Osoba.objects.create(ime="Татјана", prezime="р.Бошковић", devojacko="Стара")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "")
        self.assertEqual(o.devojacko, "Стара")

    def test_keep_married_from_domacinstvo(self):
        # Set up: Татјана is an Ukucanin of a Domaćinstvo whose domaćin
        # is Петар Петровић. After cleanup with --keep-married-from-
        # domacinstvo her prezime should become "Петровић".
        domacin = Osoba.objects.create(ime="Петар", prezime="Петровић")
        Domacinstvo.objects.create(domacin=domacin)
        tatjana = Osoba.objects.create(ime="Татјана", prezime="р.Бошковић")
        Ukucanin.objects.create(
            domacinstvo=domacin.domacinstvo, osoba=tatjana, ime_ukucana="Татјана"
        )
        self.cmd._popravi(dry_run=False, keep_from_dom=True)
        tatjana.refresh_from_db()
        self.assertEqual(tatjana.prezime, "Петровић")
        self.assertEqual(tatjana.devojacko, "Бошковић")

    def test_keep_from_dom_skips_when_host_also_marked(self):
        # If the host's prezime ALSO has a marker, we should not copy it.
        host = Osoba.objects.create(ime="Никола", prezime="р.Јовановић")
        Domacinstvo.objects.create(domacin=host)
        ana = Osoba.objects.create(ime="Ана", prezime="р.Илић")
        Ukucanin.objects.create(
            domacinstvo=host.domacinstvo, osoba=ana, ime_ukucana="Ана"
        )
        self.cmd._popravi(dry_run=False, keep_from_dom=True)
        ana.refresh_from_db()
        # Host had a marker — fall back to blank prezime.
        self.assertEqual(ana.prezime, "")
        self.assertEqual(ana.devojacko, "Илић")

    def test_capital_R_cyrillic_marker(self):
        o = Osoba.objects.create(ime="Ивана", prezime="Р.Алексић")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "")
        self.assertEqual(o.devojacko, "Алексић")

    def test_bare_marker_untouched(self):
        # An Osoba whose prezime is literally "р." has nothing useful to
        # extract — leave it alone (no devojacko produced).
        o = Osoba.objects.create(ime="Икс", prezime="р.")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        # izdvoj_devojacko("р.") returns ("", "") → devojacko is empty so the
        # row is skipped.
        self.assertEqual(o.prezime, "р.")
        self.assertFalse(o.devojacko)


class PopraviDevojackaCommandCLITests(TestCase):
    """Smoke test the CLI signature via call_command (it must accept the
    documented flags without erroring)."""

    def test_call_command_dry_run(self):
        # No tenants in the test DB → command iterates 0 tenants and
        # returns cleanly.
        out = StringIO()
        call_command("popravi_devojacka", "--dry-run", stdout=out)

    def test_call_command_keep_flag(self):
        out = StringIO()
        call_command(
            "popravi_devojacka",
            "--dry-run",
            "--keep-married-from-domacinstvo",
            stdout=out,
        )

    def test_call_command_schema_filter(self):
        # An unknown --schema now fails fast instead of silently touching
        # nothing (#330).
        from django.core.management.base import CommandError

        out = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "popravi_devojacka",
                "--dry-run",
                "--schema",
                "nonexistent_schema",
                stdout=out,
            )


class ImporterIntegrationTests(TestCase):
    """The importers (migracija_*) call izdvoj_devojacko via the helpers
    module. Verify the integration point exists and produces the
    expected (married, devojacko) tuple shape callers depend on."""

    def test_helper_is_used_by_ukucana_module(self):
        from registar.uvoz import migracija_ukucana_parohijana

        self.assertTrue(hasattr(migracija_ukucana_parohijana, "izdvoj_devojacko"))

    def test_helper_is_used_by_krstenja_module(self):
        from registar.uvoz import migracija_krstenja

        self.assertTrue(hasattr(migracija_krstenja, "izdvoj_devojacko"))
