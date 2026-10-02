"""Увоз крштења (registar.uvoz.krstenja): прескакање, дупликати, особе, адресе."""

from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.models import Krstenje
from registar.uvoz import krstenja
from registar.uvoz.krstenja import SOURCE_COLUMNS
from registar.uvoz.krstenja import Command as MigracijaKrstenja


def _red(sifra, **polja):
    """Ред staging табеле са подразумеваним дететом и оцем."""
    row = {c: "" for c in SOURCE_COLUMNS}
    row.update(
        K_SIFRA=str(sifra),
        K_AKTGOD="2000",
        K_PROTST=str(sifra),
        K_RODJGOD="1999",
        K_RODJMESE="12",
        K_RODJDAN="1",
        K_KRSGOD="2000",
        K_KRSMESE="2",
        K_KRSDAN="3",
        K_DETIME="Лука",
        K_DETPOL="1",
        K_RODIME="Марко",
        K_RODPREZ="Лукић",
        K_ROD2IME="Мара",
        K_RBRSVE="0",
    )
    row.update(polja)
    return [row[c] for c in SOURCE_COLUMNS]


class UvozKrstenjaTests(TestCase):
    """Понашање команде над малом staging табелом."""

    def setUp(self):
        from registar.utils.migracija.address import _cache
        from registar.utils.migracija.osoba_repo import _OSOBA_CACHE_BY_SCHEMA

        _cache().clear()
        _OSOBA_CACHE_BY_SCHEMA.clear()

    def _staging(self, *redovi):
        cols = ", ".join(f'"{c}" TEXT' for c in SOURCE_COLUMNS)
        placeholders = ", ".join(["%s"] * len(SOURCE_COLUMNS))
        with connection.cursor() as cur:
            cur.execute(f"CREATE TEMPORARY TABLE hsp_krstenja ({cols})")
            for red in redovi:
                cur.execute(f"INSERT INTO hsp_krstenja VALUES ({placeholders})", red)

    def _uvezi(self, **opts):
        out = StringIO()
        call_command(MigracijaKrstenja(), stdout=out, **opts)
        return out.getvalue()

    def _staging_postoji(self):
        with connection.cursor() as cur:
            cur.execute("SELECT to_regclass('hsp_krstenja')")
            return cur.fetchone()[0] is not None

    def test_missing_child_name_is_skipped(self):
        """Ред без имена детета се прескаче, остали улазе."""
        self._staging(_red(1), _red(2, K_DETIME=""))
        out = self._uvezi()
        self.assertEqual(Krstenje.objects.count(), 1)
        self.assertIn("недостаје име детета или презиме оца", out)

    def test_source_duplicates_are_skipped_and_counted(self):
        """Исти протокол, дете и датум улазе само једном."""
        self._staging(_red(1), _red(1))
        out = self._uvezi()
        self.assertEqual(Krstenje.objects.count(), 1)
        self.assertIn("дупликат — иста citation + дете + датум", out)
        self.assertIn("Прескочено као дупликати у извору: 1", out)

    def test_people_and_flags(self):
        """Дете носи презиме оца; мајка девојачко презиме; заставице из "1"."""
        self._staging(
            _red(
                1,
                K_DETPOL="2",
                K_ROD2PREZ="рођ. Марић",
                K_DETZIVO="1",
                K_DETBLIZ="1",
                K_DETBLIZ2="Ана",
                K_DETIMEG="Леа",
            )
        )
        self._uvezi()
        k = Krstenje.objects.get()
        self.assertEqual(
            (k.dete.ime, k.dete.prezime, k.dete.pol), ("Лука", "Лукић", "Ж")
        )
        self.assertEqual((k.otac.ime, k.otac.pol), ("Марко", "М"))
        self.assertEqual(k.majka.pol, "Ж")
        self.assertEqual((k.majka.prezime, k.majka.devojacko), ("Лукић", "Марић"))
        self.assertTrue(k.zivorodjeno)
        self.assertTrue(k.blizanac)
        self.assertFalse(k.vanbracno)
        self.assertEqual(k.ime_blizanca, "Ана")
        k.dete.refresh_from_db()
        self.assertEqual(k.dete.gradjansko_ime, "Леа")

    def test_kum_with_and_without_surname_column(self):
        """Кум из два поља или из пуног имена; неуспело цепање уз --verbose-errors."""
        self._staging(
            _red(1, K_KUMIME="Јован", K_KUMPREZ="Јовић"),
            _red(2, K_DETIME="Ана", K_KUMIME="Петар Перић"),
            _red(3, K_DETIME="Ива", K_KUMIME="Јован"),
        )
        out = self._uvezi(verbose_errors=True)
        kumovi = {
            k.redni_broj: (k.kum.ime, k.kum.prezime) if k.kum else None
            for k in Krstenje.objects.all()
        }
        self.assertEqual(kumovi[1], ("Јован", "Јовић"))
        self.assertEqual(kumovi[2], ("Петар", "Перић"))
        self.assertIsNone(kumovi[3])
        self.assertIn("Неуспело цепање имена кума: 'Јован'", out)

    def test_addresses_are_attached(self):
        """Адресе детета, родитеља и кума се праве из одговарајућих колона."""
        self._staging(
            _red(
                1,
                K_IZ="Београд",
                K_ULICA="Стругарска",
                K_BROJ="5",
                K_RODMEST="Чачак",
                K_ROD2MEST="Ваљево",
                K_KUMIME="Јован Јовић",
                K_KUMMEST="Шабац",
            )
        )
        self._uvezi()
        k = Krstenje.objects.get()
        self.assertEqual(
            (k.dete.adresa.ulica, k.dete.adresa.broj, k.dete.adresa.mesto),
            ("Стругарска", "5", "Београд"),
        )
        self.assertEqual(k.otac.adresa.mesto, "Чачак")
        self.assertEqual(k.majka.adresa.mesto, "Ваљево")
        self.assertEqual(k.kum.adresa.mesto, "Шабац")

    def test_dry_run_writes_nothing_and_keeps_staging(self):
        """--dry-run не уписује крштења и не брише staging табелу."""
        self._staging(_red(1))
        out = self._uvezi(dry_run=True)
        self.assertEqual(Krstenje.objects.count(), 0)
        self.assertIn("1 нових уноса", out)
        self.assertTrue(self._staging_postoji())

    def test_parse_row_dates_default_zero_parts(self):
        """Нулти делови датума постају 1900 / 1 / 1."""
        red = _red(1, K_RODJGOD="0", K_RODJMESE="0", K_RODJDAN="0")
        zapis = krstenja.parse_row(tuple(red))
        self.assertEqual(str(zapis.rodjenje_datum), "1900-01-01")
        self.assertEqual(str(zapis.krstenje_datum), "2000-02-03")
