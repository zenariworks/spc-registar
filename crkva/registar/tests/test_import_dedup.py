"""Tests for safety-checked dedup in migracija_ukucana_parohijana."""

from django.test import TestCase
from registar.models import Osoba
from registar.utils.migracija.osoba_repo import (
    cache_osoba,
    lookup_all_osoba,
    lookup_osoba,
    nadji_osobu,
    warm_osoba_cache,
)


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


class LookupAllOsobaTest(TestCase):
    """Multiple same-name Osobe should all be discoverable via lookup_all_osoba."""

    def test_returns_all_with_same_name(self):
        a = Osoba.objects.create(ime="Бранко", prezime=".", tel_fiksni="+38111111")
        b = Osoba.objects.create(ime="Бранко", prezime=".", tel_fiksni="+38122222")
        warm_osoba_cache()
        all_ = lookup_all_osoba("Бранко", ".")
        self.assertEqual({o.pk for o in all_}, {a.pk, b.pk})

    def test_cache_osoba_is_idempotent_on_pk(self):
        o = Osoba.objects.create(ime="Тест", prezime="Тестић")
        warm_osoba_cache()
        cache_osoba(o)
        cache_osoba(o)  # second call must not duplicate
        self.assertEqual(len(lookup_all_osoba("Тест", "Тестић")), 1)


class FindMatchingOsobaTest(TestCase):
    """nadji_osobu must scan ALL same-name candidates for a signal match."""

    def test_picks_candidate_sharing_address(self):
        from registar.models import Adresa

        addr_a = Adresa.objects.create(ulica="Прва", broj="1", mesto="Чукарица")
        addr_b = Adresa.objects.create(ulica="Друга", broj="2", mesto="Чукарица")
        Osoba.objects.create(ime="Бранко", prezime=".", adresa=addr_a)
        second = Osoba.objects.create(ime="Бранко", prezime=".", adresa=addr_b)
        warm_osoba_cache()
        # Should pick `second` because its adresa matches.
        match = nadji_osobu("Бранко", ".", adresa=addr_b)
        self.assertEqual(match.pk, second.pk)

    def test_returns_none_when_nothing_shares_signal(self):
        Osoba.objects.create(ime="Никола", prezime="Петровић", tel_fiksni="+38111")
        warm_osoba_cache()
        self.assertIsNone(nadji_osobu("Никола", "Петровић", tel_f="+38122"))

    def test_returns_none_for_blank_names(self):
        self.assertIsNone(nadji_osobu("", "."))


class ImporterSafetyCheckedDedup(TestCase):
    """Run the parohijan creation loop directly and assert safe-merge behaviour."""

    def setUp(self):
        # The migracija helpers keep module-level caches that survive across
        # tests; clear them so a previous test's Adresa/Osoba refs don't leak in.
        from registar.utils.migracija.address import _cache, warm_adresa_cache
        from registar.utils.migracija.osoba_repo import (
            _OSOBA_CACHE_BY_SCHEMA,
            warm_osoba_cache,
        )

        _cache().clear()
        _OSOBA_CACHE_BY_SCHEMA.clear()
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
        from registar.uvoz.ukucani_parohijani import Command

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
        from registar.uvoz.ukucani_parohijani import Command

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

    def test_three_rows_two_share_signal_dedups_into_two(self):
        """Row #1 has signal A; rows #2 and #3 share signal B → should end up
        with 2 Osobe (not 3). Regression for the bug where the cache only
        held the first same-name Osoba and #3 was never compared against #2.
        """
        from django.db import connection
        from registar.uvoz.ukucani_parohijani import Command

        self._create_staging_table()
        with connection.cursor() as cur:
            cur.execute("""
                INSERT INTO hsp_domacini VALUES
                  (3630, 'Бранко .', NULL, '1',  '', '3/12', '+381628143626', NULL, NULL, NULL, NULL, ''),
                  (3632, 'Бранко .', NULL, '21', '', '',     '+381641296472', NULL, NULL, NULL, NULL, ''),
                  (3634, 'Бранко .', NULL, '21', '', '',     '+381641296472', NULL, NULL, NULL, NULL, '')
            """)

        cmd = Command()
        cmd._dry_run = False
        cmd.stdout = type("S", (), {"write": lambda self, *a, **k: None})()
        cmd.ulice_cache = {}
        cmd._create_parohijani_and_domacinstva()

        brankos = Osoba.objects.filter(ime="Бранко", prezime=".")
        self.assertEqual(
            brankos.count(),
            2,
            "row #2 + #3 share phone → should merge; row #1 stays separate",
        )
