"""Tests for safety-checked dedup in migracija_ukucana_parohijana."""

from django.test import TestCase
from registar.migracija.osoba_repo import lookup_osoba, warm_osoba_cache
from registar.models import Osoba


class LookupOsobaCacheTest(TestCase):
    """lookup_osoba must hit the warmed cache by (ime, prezime)."""

    def test_returns_none_for_blank(self):
        warm_osoba_cache()
        self.assertIsNone(lookup_osoba("", "Марковић"))
        self.assertIsNone(lookup_osoba("Марко", ""))
        self.assertIsNone(lookup_osoba(None, None))

    def test_returns_existing_osoba(self):
        o = Osoba.objects.create(ime="Марко", prezime="Марковић")
        warm_osoba_cache()
        found = lookup_osoba("Марко", "Марковић")
        self.assertIsNotNone(found)
        self.assertEqual(found.pk, o.pk)

    def test_case_insensitive_match(self):
        Osoba.objects.create(ime="Марко", prezime="Марковић")
        warm_osoba_cache()
        self.assertIsNotNone(lookup_osoba("марко", "МАРКОВИЋ"))

    def test_unknown_name_returns_none(self):
        Osoba.objects.create(ime="Марко", prezime="Марковић")
        warm_osoba_cache()
        self.assertIsNone(lookup_osoba("Petar", "Petrović"))


class ImporterSafetyCheckedDedup(TestCase):
    """Run the parohijan creation loop directly and assert safe-merge behaviour."""

    def setUp(self):
        # The migracija helpers keep module-level caches that survive across
        # tests; clear them so a previous tests Adresa/Osoba refs dont leak in.
        from registar.migracija.address import _ADRESA_CACHE, warm_adresa_cache
        from registar.migracija.osoba_repo import _OSOBA_CACHE, warm_osoba_cache

        _ADRESA_CACHE.clear()
        _OSOBA_CACHE.clear()
        warm_adresa_cache()
        warm_osoba_cache()

    def _create_staging_table(self):
        from django.db import connection

        with connection.cursor() as cur:
            cur.execute("""
                CREATE TEMPORARY TABLE hsp_domacini (
                    "DOM_RBR" INT, "DOM_IME" VARCHAR(200), "DOM_RBRUL" INT,
                    "DOM_BROJ" VARCHAR(10), "DOM_OZNAKA" VARCHAR(10),
                    "DOM_STAN" VARCHAR(10), "DOM_TELDIR" VARCHAR(40),
                    "DOM_TELMOB" VARCHAR(40), "DOM_RBRSL" INT,
                    "DOM_SLAVOD" VARCHAR(1), "DOM_USKVOD" VARCHAR(1),
                    "DOM_NAPOM" TEXT
                )
            """)
            cur.execute("""
                CREATE TEMPORARY TABLE hsp_ukucani (
                    "UK_RBRDOM" INT, "UK_IME" VARCHAR(200)
                )
            """)
            cur.execute(
                'CREATE TEMPORARY TABLE hsp_ulice ("UL_SIFRA" INT, "UL_NAZIV" VARCHAR(200))'
            )

    def test_same_name_same_phone_merges_into_one_osoba(self):
        """Two DBF rows with identical name + tel_fiksni → one Osoba."""
        from django.db import connection
        from registar.management.commands.migracija_ukucana_parohijana import Command

        self._create_staging_table()
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO hsp_domacini VALUES
                  (10, 'Драган Станчић', NULL, '12', '', '', '+3812544899', NULL, NULL, NULL, NULL, ''),
                  (583, 'Драган Станчић', NULL, '12', '', '', '+3812544899', NULL, NULL, NULL, NULL, '')
            """)

        cmd = Command()
        cmd._dry_run = False
        cmd.stdout = type("S", (), {"write": lambda self, *a, **k: None})()
        cmd.ulice_cache = {}
        cmd._create_parohijani_and_domacinstva()

        dragans = Osoba.objects.filter(ime="Драган", prezime="Станчић")
        self.assertEqual(
            dragans.count(), 1, "should dedup to one Osoba on shared phone"
        )

    def test_same_name_different_phones_keeps_both(self):
        """Two DBF rows with same name but different phones → two Osobe."""
        from django.db import connection
        from registar.management.commands.migracija_ukucana_parohijana import Command

        self._create_staging_table()
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO hsp_domacini VALUES
                  (10, 'Никола Петровић', NULL, '12', '', '', '+38111111', NULL, NULL, NULL, NULL, ''),
                  (583, 'Никола Петровић', NULL, '34', '', '', '+38122222', NULL, NULL, NULL, NULL, '')
            """)

        cmd = Command()
        cmd._dry_run = False
        cmd.stdout = type("S", (), {"write": lambda self, *a, **k: None})()
        cmd.ulice_cache = {}
        cmd._create_parohijani_and_domacinstva()

        nikolas = Osoba.objects.filter(ime="Никола", prezime="Петровић")
        self.assertEqual(nikolas.count(), 2, "different phones → don't merge")
