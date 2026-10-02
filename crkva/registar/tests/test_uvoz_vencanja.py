"""Увоз венчања (registar.uvoz.vencanja): прескакање, сродници, пакети, dry-run."""

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.models import Vencanje
from registar.uvoz import vencanja
from registar.uvoz.vencanja import SOURCE_COLUMNS
from registar.uvoz.vencanja import Command as MigracijaVencanja


def _red(sifra, **polja):
    """Ред staging табеле са подразумеваним женихом и невестом."""
    row = {c: "" for c in SOURCE_COLUMNS}
    row.update(
        V_SIFRA=str(sifra),
        V_AKTGOD="2001",
        V_Z_IME="Марко",
        V_Z_PREZ="Марковић",
        V_N_IME="Ана",
        V_N_PREZ="Анић",
        V_RBRSVEST="0",
    )
    row.update(polja)
    return [row[c] for c in SOURCE_COLUMNS]


class UvozVencanjaTests(TestCase):
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
            cur.execute(f"CREATE TEMPORARY TABLE hsp_vencanja ({cols})")
            for red in redovi:
                cur.execute(f"INSERT INTO hsp_vencanja VALUES ({placeholders})", red)

    def _uvezi(self, **opts):
        out = StringIO()
        call_command(MigracijaVencanja(), stdout=out, **opts)
        return out.getvalue()

    def _staging_postoji(self):
        with connection.cursor() as cur:
            cur.execute("SELECT to_regclass('hsp_vencanja')")
            return cur.fetchone()[0] is not None

    def test_incomplete_names_are_skipped(self):
        """Ред без имена невесте се прескаче, остали улазе."""
        self._staging(_red(1, V_TEKBROJ="1"), _red(2, V_TEKBROJ="2", V_N_IME=""))
        out = self._uvezi()
        self.assertEqual(Vencanje.objects.count(), 1)
        self.assertIn("непотпуна имена женика/невесте", out)

    def test_bride_gets_groom_surname_and_maiden_name(self):
        """Невеста добија презиме женика, а своје као девојачко (#332)."""
        self._staging(_red(1))
        self._uvezi()
        v = Vencanje.objects.get()
        self.assertEqual((v.zenik.prezime, v.zenik.pol), ("Марковић", "М"))
        self.assertEqual(
            (v.nevesta.prezime, v.nevesta.devojacko, v.nevesta.pol),
            ("Марковић", "Анић", "Ж"),
        )

    def test_relatives_are_linked_with_expected_sex(self):
        """Родитељи добијају задат пол, кум и стари сват пол по имену."""
        self._staging(
            _red(
                1,
                V_ZR_OTAC="Петар Марковић",
                V_ZR_MAJKA="Мара Марковић",
                V_NR_OTAC="Јован Анић",
                V_NR_MAJKA="Јелена Анић",
                V_KUM="Милица Кумић",
                V_SSVAT="Стеван Сватић, Београд",
            )
        )
        self._uvezi()
        v = Vencanje.objects.get()
        self.assertEqual((v.svekar.ime, v.svekar.pol), ("Петар", "М"))
        self.assertEqual((v.svekrva.ime, v.svekrva.pol), ("Мара", "Ж"))
        self.assertEqual((v.tast.ime, v.tast.pol), ("Јован", "М"))
        self.assertEqual((v.tasta.ime, v.tasta.pol), ("Јелена", "Ж"))
        self.assertEqual(
            (v.kum.ime, v.kum.prezime, v.kum.pol), ("Милица", "Кумић", "Ж")
        )
        self.assertEqual((v.stari_svat.ime, v.stari_svat.prezime), ("Стеван", "Сватић"))

    def test_unsplittable_kum_is_reported_only_when_verbose(self):
        """Неуспело цепање кума се пријављује само уз --verbose-errors."""
        self._staging(_red(1, V_KUM="кум", V_ZR_OTAC="отац"))
        out = self._uvezi(verbose_errors=True)
        v = Vencanje.objects.get()
        self.assertIsNone(v.kum)
        self.assertIsNone(v.svekar)
        self.assertIn("Неуспело цепање имена (кум): 'кум'", out)
        self.assertNotIn("отац", out)

    def test_unsplittable_kum_is_silent_by_default(self):
        """Без --verbose-errors нема упозорења о цепању имена."""
        self._staging(_red(1, V_KUM="кум"))
        self.assertNotIn("Неуспело цепање", self._uvezi())

    def test_batches_report_progress(self):
        """Пун пакет се уписује и пријављује напредак."""
        self._staging(*(_red(i, V_TEKBROJ=str(i)) for i in range(1, 4)))
        with mock.patch.object(MigracijaVencanja, "BATCH_SIZE", 2):
            out = self._uvezi()
        self.assertEqual(Vencanje.objects.count(), 3)
        self.assertIn("Обрађено 2 записа...", out)
        self.assertFalse(self._staging_postoji())

    def test_dry_run_writes_nothing_and_keeps_staging(self):
        """--dry-run не уписује венчања и не брише staging табелу."""
        self._staging(_red(1))
        out = self._uvezi(dry_run=True)
        self.assertEqual(Vencanje.objects.count(), 0)
        self.assertIn("DRY RUN", out)
        self.assertTrue(self._staging_postoji())

    def test_parse_row_reads_date_triples(self):
        """Датуми се читају из тројки колона година/месец/дан."""
        red = _red(
            1,
            V_GODINA="2001",
            V_MESEC="6",
            V_DAN="9",
            V_Z_RODJG="1975",
            V_Z_RODJM="1",
            V_Z_RODJD="2",
            V_ISPITGOD="2001",
            V_ISPITMES="5",
            V_ISPITDAN="30",
        )
        zapis = vencanja.parse_row(tuple(red))
        self.assertEqual(str(zapis.datum), "2001-06-09")
        self.assertEqual(str(zapis.zenik_datum_rodj), "1975-01-02")
        self.assertEqual(str(zapis.datum_ispita), "2001-05-30")
        self.assertIsNone(zapis.nevesta_datum_rodj)
