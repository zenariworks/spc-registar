"""Команда migracija_ulice_svestenik: DBF читач и додела свештеника улицама (#26)."""

import struct
import tempfile
import zipfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from registar.management.commands.migracija_ulice_svestenik import _norm, _read_dbf
from registar.models import Adresa, Svestenik

ULICE_POLJA = [("UL_NAZIV", "C", 30), ("UL_RBRSV", "I", 4)]


def _dbf(polja, zapisi):
    """Гради DBF у меморији: `zapisi` су (обрисан, [бајтови по пољу])."""
    rlen = 1 + sum(flen for _, _, flen in polja)
    hlen = 32 + 32 * len(polja) + 1
    header = bytearray(32)
    header[0] = 0x03
    header[4:12] = struct.pack("<IHH", len(zapisi), hlen, rlen)
    for name, ftype, flen in polja:
        opis = bytearray(32)
        opis[0:11] = name.encode("ascii").ljust(11, b"\x00")
        opis[11] = ord(ftype)
        opis[16] = flen
        header += opis
    header += b"\x0d"
    telo = b"".join(
        (b"\x2a" if obrisan else b" ") + b"".join(vrednosti)
        for obrisan, vrednosti in zapisi
    )
    return bytes(header) + telo + b"\x1a"


def _ulica(naziv, rbrsv, obrisan=False):
    """Запис HSPULICE са називом (cp1250) и шифром свештеника."""
    return (
        obrisan,
        [naziv.encode("cp1250").ljust(30), struct.pack("<i", rbrsv)],
    )


class ReadDbfTests(SimpleTestCase):
    """Минимални DBF читач."""

    def test_reads_string_and_int_fields(self):
        """C поље се декодира и стрипује, I поље је little-endian int."""
        raw = _dbf(ULICE_POLJA, [_ulica("  Strugarska ", 7)])
        self.assertEqual(_read_dbf(raw), [{"UL_NAZIV": "Strugarska", "UL_RBRSV": 7}])

    def test_skips_deleted_records(self):
        """Записи означени као обрисани (0x2A) се прескачу."""
        raw = _dbf(ULICE_POLJA, [_ulica("Prva", 1, obrisan=True), _ulica("Druga", 2)])
        self.assertEqual([r["UL_NAZIV"] for r in _read_dbf(raw)], ["Druga"])

    def test_other_types_are_stripped_text(self):
        """Остали типови се враћају као стрипован текст."""
        raw = _dbf([("BROJ", "N", 5)], [(False, [b"   42"])])
        self.assertEqual(_read_dbf(raw), [{"BROJ": "42"}])

    def test_string_field_drops_nul_padding(self):
        """Нул бајтови на крају C поља се одбацују."""
        raw = _dbf([("IME", "C", 6)], [(False, [b"Ana\x00\x00\x00"])])
        self.assertEqual(_read_dbf(raw), [{"IME": "Ana"}])

    def test_decodes_cp1250(self):
        """Називи се декодирају као cp1250, исто као load_dbf."""
        raw = _dbf(ULICE_POLJA, [_ulica("Šumadijska", 3)])
        self.assertEqual(_read_dbf(raw)[0]["UL_NAZIV"], "Šumadijska")


class NormTests(SimpleTestCase):
    """Кључ за поклапање назива улица."""

    def test_collapses_whitespace_and_lowercases(self):
        """Вишак размака се сажима, а велика слова спуштају."""
        self.assertEqual(_norm("  Макишка   Колонија "), "макишка колонија")

    def test_none_is_empty(self):
        """Празан назив даје празан кључ."""
        self.assertEqual(_norm(None), "")


class UliceSvestenikCommandTests(TestCase):
    """Додела свештеника адресама по називу улице."""

    @classmethod
    def setUpTestData(cls):
        cls.marko = Svestenik.objects.create(
            uid=11, ime="Марко", prezime="Марковић", zvanje="јереј"
        )
        cls.petar = Svestenik.objects.create(
            uid=12, ime="Петар", prezime="Петровић", zvanje="јереј"
        )
        cls.strugarska = [
            Adresa.objects.create(ulica="Стругарска", broj=str(b)) for b in (1, 2)
        ]
        cls.vec_dodeljena = Adresa.objects.create(
            ulica="Стругарска", broj="3", svestenik=cls.marko
        )
        cls.kolubarska = Adresa.objects.create(ulica="Колубарска", broj="1")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.zip_path = Path(self.tmp.name) / "crkva.zip"
        raw = _dbf(
            ULICE_POLJA,
            [
                _ulica("Strugarska", 11),
                _ulica("Kolubarska", 11),
                _ulica("Kolubarska", 12),
                _ulica("Nepoznata", 12),
                _ulica("Daleka", 99),
                _ulica("Neraspodeljena", 0),
                _ulica("Obrisana", 12, obrisan=True),
            ],
        )
        with zipfile.ZipFile(self.zip_path, "w") as z:
            z.writestr("dbf/hspulice.dbf", raw)

    def _pokreni(self, *args):
        out = StringIO()
        call_command(
            "migracija_ulice_svestenik",
            "--zip",
            str(self.zip_path),
            "--schema",
            "test_tenant",
            *args,
            stdout=out,
        )
        return out.getvalue()

    def test_assigns_priest_to_matching_street(self):
        """Све адресе поклопљене улице добијају свештеника."""
        out = self._pokreni()
        for adresa in self.strugarska:
            adresa.refresh_from_db()
            self.assertEqual(adresa.svestenik_id, self.marko.uid)
        self.assertIn("Улица са додељеним свештеником у старој бази: 4", out)
        self.assertIn("Стругарска → Марко Марковић (3 адр.)", out)
        self.assertIn("Поклопљено улица: 1; ажурирано адреса: 2", out)

    def test_dry_run_writes_nothing(self):
        """--dry-run приказује план без уписа."""
        out = self._pokreni("--dry-run")
        for adresa in self.strugarska:
            adresa.refresh_from_db()
            self.assertIsNone(adresa.svestenik_id)
        self.assertIn("[DRY-RUN] Поклопљено улица: 1; ажурирано адреса: 2", out)

    def test_split_street_is_skipped(self):
        """Улица подељена међу свештеницима се не додељује."""
        out = self._pokreni()
        self.kolubarska.refresh_from_db()
        self.assertIsNone(self.kolubarska.svestenik_id)
        self.assertIn("Подељене улице — прескочене, додела ручно (1): Колубарска", out)

    def test_reports_unmatched_streets_and_priests(self):
        """Неупарене улице и непознати свештеници се пријављују."""
        out = self._pokreni()
        self.assertIn("Неупарене улице (1): Непозната", out)
        self.assertIn("Без свештеника у новој бази (1): Далека#99", out)
