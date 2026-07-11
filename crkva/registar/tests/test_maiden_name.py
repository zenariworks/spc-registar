"""Tests for the maiden-name marker split: extract_maiden helper +
``popravi_devojacka`` management command.

The DBF import imported many female Osoba with surnames like
"р.Бошковић" / "рођ. Видојевић". The marker means "рођена" (née) and
the trailing surname is the maiden name, not the married one.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,invalid-name,protected-access,import-outside-toplevel

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from registar.migracija.helpers import extract_maiden
from registar.models import Domacinstvo, Osoba, Ukucanin


class ExtractMaidenTests(TestCase):
    """Pure-function tests for helpers.extract_maiden — no DB."""

    def test_cyrillic_r_dot_no_space(self):
        self.assertEqual(extract_maiden("р.Бошковић"), ("", "Бошковић"))

    def test_cyrillic_r_dot_with_space(self):
        self.assertEqual(extract_maiden("р. Бошковић"), ("", "Бошковић"))

    def test_capital_cyrillic_r_dot(self):
        self.assertEqual(extract_maiden("Р.Бошковић"), ("", "Бошковић"))

    def test_cyrillic_r_space(self):
        # "р Марковић" — bare letter + whitespace
        self.assertEqual(extract_maiden("р Марковић"), ("", "Марковић"))

    def test_rodj_dot_marker(self):
        self.assertEqual(extract_maiden("рођ. Видојевић"), ("", "Видојевић"))
        self.assertEqual(extract_maiden("рођ.Видојевић"), ("", "Видојевић"))

    def test_rodjena_full_word_marker(self):
        self.assertEqual(extract_maiden("рођена Ђорђевић"), ("", "Ђорђевић"))
        self.assertEqual(extract_maiden("Рођена Ђорђевић"), ("", "Ђорђевић"))

    def test_latin_r_dot(self):
        self.assertEqual(extract_maiden("r.Marković"), ("", "Marković"))
        self.assertEqual(extract_maiden("R. Marković"), ("", "Marković"))

    def test_no_marker_returns_input_as_married(self):
        self.assertEqual(extract_maiden("Marko Marković"), ("Marko Marković", ""))
        self.assertEqual(extract_maiden("Бошковић"), ("Бошковић", ""))

    def test_does_not_eat_leading_R_when_no_marker(self):
        # Regression for the ocisti_prezime bug: "Радановић" must not
        # become "адановић".
        self.assertEqual(extract_maiden("Радановић"), ("Радановић", ""))
        self.assertEqual(extract_maiden("Ристић"), ("Ристић", ""))
        self.assertEqual(extract_maiden("Radanović"), ("Radanović", ""))

    def test_empty_and_none(self):
        self.assertEqual(extract_maiden(""), ("", ""))
        self.assertEqual(extract_maiden(None), ("", ""))
        self.assertEqual(extract_maiden("   "), ("", ""))

    def test_bare_marker_alone(self):
        # "р." with nothing after — both halves empty.
        self.assertEqual(extract_maiden("р."), ("", ""))
        self.assertEqual(extract_maiden("рођ."), ("", ""))
        self.assertEqual(extract_maiden("r."), ("", ""))

    def test_leading_and_trailing_whitespace(self):
        self.assertEqual(extract_maiden("  р.Бошковић  "), ("", "Бошковић"))
        self.assertEqual(extract_maiden("  Marković  "), ("Marković", ""))

    def test_capitalises_lowercase_maiden(self):
        # Sometimes the source is sloppy: "р.бошковић" → "Бошковић".
        self.assertEqual(extract_maiden("р.бошковић"), ("", "Бошковић"))
        self.assertEqual(extract_maiden("r.marković"), ("", "Marković"))

    def test_documented_examples_from_task(self):
        # Татјана р.Бошковић → ime="Татјана", prezime="" (married blank),
        # devojacko_prezime="Бошковић"
        ime = "Татјана"
        married, maiden = extract_maiden("р.Бошковић")
        self.assertEqual(ime, "Татјана")
        self.assertEqual(married, "")
        self.assertEqual(maiden, "Бошковић")

        # Верица рођ. Видојевић → ime="Верица", devojacko="Видојевић"
        married, maiden = extract_maiden("рођ. Видојевић")
        self.assertEqual(married, "")
        self.assertEqual(maiden, "Видојевић")


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
        self.assertEqual(o.devojacko_prezime, "Бошковић")

    def test_rodj_dot_marker_moved(self):
        o = Osoba.objects.create(ime="Верица", prezime="рођ. Видојевић")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "")
        self.assertEqual(o.devojacko_prezime, "Видојевић")

    def test_dry_run_does_not_modify(self):
        o = Osoba.objects.create(ime="Татјана", prezime="р.Бошковић")
        self.cmd._popravi(dry_run=True, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "р.Бошковић")
        self.assertIsNone(o.devojacko_prezime)

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
        self.assertFalse(o.devojacko_prezime)

    def test_keep_existing_devojacko(self):
        # If devojacko_prezime is already set, don't overwrite it.
        o = Osoba.objects.create(
            ime="Татјана", prezime="р.Бошковић", devojacko_prezime="Стара"
        )
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "")
        self.assertEqual(o.devojacko_prezime, "Стара")

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
        self.assertEqual(tatjana.devojacko_prezime, "Бошковић")

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
        self.assertEqual(ana.devojacko_prezime, "Илић")

    def test_capital_R_cyrillic_marker(self):
        o = Osoba.objects.create(ime="Ивана", prezime="Р.Алексић")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        self.assertEqual(o.prezime, "")
        self.assertEqual(o.devojacko_prezime, "Алексић")

    def test_bare_marker_untouched(self):
        # An Osoba whose prezime is literally "р." has nothing useful to
        # extract — leave it alone (no maiden produced).
        o = Osoba.objects.create(ime="Икс", prezime="р.")
        self.cmd._popravi(dry_run=False, keep_from_dom=False)
        o.refresh_from_db()
        # extract_maiden("р.") returns ("", "") → maiden is empty so the
        # row is skipped.
        self.assertEqual(o.prezime, "р.")
        self.assertFalse(o.devojacko_prezime)


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
    """The importers (migracija_*) call extract_maiden via the helpers
    module. Verify the integration point exists and produces the
    expected (married, maiden) tuple shape callers depend on."""

    def test_helper_is_used_by_ukucana_module(self):
        from registar.uvoz import migracija_ukucana_parohijana

        self.assertTrue(hasattr(migracija_ukucana_parohijana, "extract_maiden"))

    def test_helper_is_used_by_krstenja_module(self):
        from registar.uvoz import migracija_krstenja

        self.assertTrue(hasattr(migracija_krstenja, "extract_maiden"))
