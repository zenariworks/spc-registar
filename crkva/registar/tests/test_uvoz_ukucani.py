"""Увоз домаћинстава и укућана (registar.uvoz.ukucani_parohijani)."""

from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.models import Domacinstvo, Osoba, Slava, Ukucanin
from registar.utils.migracija.slava_map import resolve_slava
from registar.uvoz.ukucani_parohijani import Command as MigracijaUkucana

DOMACINI = (
    "DOM_RBR",
    "DOM_IME",
    "DOM_RBRUL",
    "DOM_BROJ",
    "DOM_OZNAKA",
    "DOM_STAN",
    "DOM_TELDIR",
    "DOM_TELMOB",
    "DOM_RBRSL",
    "DOM_SLAVOD",
    "DOM_USKVOD",
    "DOM_NAPOM",
)


def _domacin(rbr, ime, **polja):
    """Ред hsp_domacini са празним пољима осим задатих."""
    red = {c: None for c in DOMACINI}
    red.update(DOM_RBR=str(rbr), DOM_IME=ime)
    red.update(polja)
    return [red[c] for c in DOMACINI]


class UvozUkucanaTests(TestCase):
    """Понашање команде над малим staging табелама."""

    def setUp(self):
        from registar.utils.migracija.address import _cache
        from registar.utils.migracija.osoba_repo import _OSOBA_CACHE_BY_SCHEMA

        _cache().clear()
        _OSOBA_CACHE_BY_SCHEMA.clear()

    def _staging(self, domacini, ukucani=(), ulice=()):
        """Привремене staging табеле са TEXT колонама, као после load_dbf."""
        kolone = ", ".join(f'"{c}" TEXT' for c in DOMACINI)
        mesta = ", ".join(["%s"] * len(DOMACINI))
        with connection.cursor() as cur:
            cur.execute(f"CREATE TEMPORARY TABLE hsp_domacini ({kolone})")
            cur.execute(
                'CREATE TEMPORARY TABLE hsp_ukucani ("UK_RBRDOM" TEXT, "UK_IME" TEXT)'
            )
            cur.execute(
                'CREATE TEMPORARY TABLE hsp_ulice ("UL_SIFRA" TEXT, "UL_NAZIV" TEXT)'
            )
            for red in domacini:
                cur.execute(f"INSERT INTO hsp_domacini VALUES ({mesta})", red)
            for red in ukucani:
                cur.execute("INSERT INTO hsp_ukucani VALUES (%s, %s)", red)
            for red in ulice:
                cur.execute("INSERT INTO hsp_ulice VALUES (%s, %s)", red)

    def _uvezi(self, **opts):
        out = StringIO()
        call_command(MigracijaUkucana(), stdout=out, **opts)
        return out.getvalue()

    def _tabela_postoji(self, naziv):
        with connection.cursor() as cur:
            cur.execute("SELECT to_regclass(%s)", [naziv])
            return cur.fetchone()[0] is not None

    def test_creates_domacin_household_and_members(self):
        """Домаћин, адреса, домаћинство и укућани из staging табела."""
        self._staging(
            [
                _domacin(
                    5,
                    "Петар Петровић",
                    DOM_RBRUL="3",
                    DOM_BROJ="12",
                    DOM_STAN="4",
                    DOM_TELDIR=" 011222 ",
                    DOM_TELMOB="",
                    DOM_RBRSL="1",
                    DOM_SLAVOD="D",
                    DOM_USKVOD="N",
                    DOM_NAPOM="напомена",
                )
            ],
            ukucani=[("5", "Ana"), ("5", "+Jovan"), ("99", "Niko"), ("5", "")],
            ulice=[("3", "Стругарска")],
        )
        out = self._uvezi()
        osoba = Osoba.objects.get(uid=5)
        self.assertEqual(
            (osoba.ime, osoba.prezime, osoba.pol), ("Петар", "Петровић", "М")
        )
        self.assertTrue(osoba.parohijan)
        self.assertEqual((osoba.tel_fiksni, osoba.tel_mobilni), ("011222", None))
        adresa = osoba.adresa
        self.assertEqual(
            (
                adresa.ulica,
                adresa.broj,
                adresa.broj_stana,
                adresa.mesto,
                adresa.primedba,
            ),
            ("Стругарска", "12", "4", "Чукарица", "напомена"),
        )
        dom = Domacinstvo.objects.get(domacin=osoba)
        self.assertEqual(dom.slava, resolve_slava(1, Slava))
        self.assertEqual((dom.slavska_vodica, dom.vaskrsnja_vodica), (True, False))
        self.assertEqual((dom.napomena, dom.adresa), ("напомена", adresa))
        clanovi = {
            (u.ime_ukucana, u.preminuo, u.osoba.prezime)
            for u in Ukucanin.objects.filter(domacinstvo=dom)
        }
        self.assertEqual(
            clanovi, {("Ана", False, "Петровић"), ("Јован", True, "Петровић")}
        )
        self.assertIn("Креирано 1 парохијана и 1 домаћинстава.", out)
        self.assertFalse(self._tabela_postoji("hsp_domacini"))
        self.assertFalse(self._tabela_postoji("hsp_ukucani"))

    def test_incomplete_name_is_skipped(self):
        """Једна реч у имену прескаче ред; празно име тихо."""
        self._staging(
            [_domacin(1, "Petar"), _domacin(2, "  "), _domacin(3, "Ana Anic")]
        )
        out = self._uvezi()
        self.assertIn("Парохијан UID 1: непотпуно име 'Петар'", out)
        self.assertEqual(Osoba.objects.filter(parohijan=True).count(), 1)

    def test_maiden_only_surname_is_used_as_surname(self):
        """Презиме само са „р.“ постаје и презиме и девојачко."""
        self._staging([_domacin(1, "Ана р.Петровић")])
        self._uvezi()
        osoba = Osoba.objects.get(uid=1)
        self.assertEqual((osoba.prezime, osoba.devojacko), ("Петровић", "Петровић"))

    def test_merge_fills_only_missing_fields(self):
        """Поклапање по телефону допуњује само празна поља постојеће особе."""
        postojeca = Osoba.objects.create(
            ime="Марко", prezime="Марковић", tel_fiksni="011", parohijan=False
        )
        self._staging(
            [_domacin(40, "Марко р.Марковић", DOM_TELDIR="011", DOM_TELMOB="064")]
        )
        out = self._uvezi()
        postojeca.refresh_from_db()
        self.assertTrue(postojeca.parohijan)
        self.assertEqual(
            (
                postojeca.tel_fiksni,
                postojeca.tel_mobilni,
                postojeca.devojacko,
                postojeca.pol,
            ),
            ("011", "064", "Марковић", "М"),
        )
        self.assertIsNotNone(postojeca.adresa_id)
        self.assertFalse(Osoba.objects.filter(uid=40).exists())
        self.assertTrue(Domacinstvo.objects.filter(domacin=postojeca).exists())
        self.assertIn("Креирано 0 парохијана и 1 домаћинстава.", out)

    def test_members_follow_merged_domacin(self):
        """Укућани два DBF реда спојена у једну особу иду у исто домаћинство."""
        self._staging(
            [
                _domacin(10, "Ivan Ivic", DOM_TELDIR="011"),
                _domacin(11, "Ivan Ivic", DOM_TELDIR="011"),
            ],
            ukucani=[("10", "Mara"), ("11", "Pera")],
        )
        self._uvezi()
        dom = Domacinstvo.objects.get()
        self.assertEqual(
            sorted(u.ime_ukucana for u in dom.ukucani.all()), ["Мара", "Пера"]
        )

    def test_bad_number_logs_error_and_continues(self):
        """Неисправан број улице бележи грешку, остали редови улазе."""
        self._staging([_domacin(1, "Ana Anic", DOM_RBRUL="x"), _domacin(2, "Ivo Ivic")])
        out = self._uvezi()
        self.assertIn("Грешка: Грешка за домаћина UID 1:", out)
        self.assertEqual(list(Osoba.objects.values_list("uid", flat=True)), [2])

    def test_dry_run_writes_nothing(self):
        """--dry-run броји, не уписује и чува staging табеле."""
        postojeci = Osoba.objects.create(ime="Стари", prezime="Домаћин")
        Domacinstvo.objects.create(domacin=postojeci)
        self._staging(
            [_domacin(1, "Ana Anic"), _domacin(2, "Ivo")], ukucani=[("1", "Mara")]
        )
        out = self._uvezi(dry_run=True)
        self.assertIn("Креирано 1 парохијана и 1 домаћинстава.", out)
        self.assertIn("DRY RUN", out)
        self.assertEqual(Domacinstvo.objects.count(), 1)
        self.assertFalse(Osoba.objects.filter(uid=1).exists())
        self.assertTrue(self._tabela_postoji("hsp_domacini"))

    def test_limit_applies_to_both_passes(self):
        """--limit ограничава и домаћине и укућане."""
        self._staging(
            [_domacin(1, "Ana Anic"), _domacin(2, "Ivo Ivic")],
            ukucani=[("1", "Mara"), ("1", "Pera"), ("2", "Zika")],
        )
        self._uvezi(limit=1)
        self.assertEqual(Domacinstvo.objects.count(), 1)
        self.assertEqual(Ukucanin.objects.count(), 1)
