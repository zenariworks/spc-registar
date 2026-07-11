"""#340: увоз крштења не сме да прави фантомског свештеника за uid=0.

``migracija_krstenja`` је радила ``get_or_create(uid=svestenik_id)`` за сваки
ред — укључујући празне (``K_RBRSVE`` = 0), па су настајали празни
``Svestenik`` редови (``__str__`` = „  ") који искачу у select2.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.models import Krstenje, Svestenik
from registar.uvoz.migracija_krstenja import SOURCE_COLUMNS as K_COLS
from registar.uvoz.migracija_krstenja import Command as MigracijaKrstenja


def _clear_caches():
    from registar.migracija.address import _cache
    from registar.migracija.osoba_repo import _OSOBA_CACHE_BY_SCHEMA

    _cache().clear()
    _OSOBA_CACHE_BY_SCHEMA.clear()


def _row(sifra, dete, prezime, rbrsve):
    r = {c: "" for c in K_COLS}
    r["K_SIFRA"] = str(sifra)
    r["K_AKTGOD"] = "2000"
    r["K_PROTST"] = str(sifra)
    r["K_RODJGOD"], r["K_RODJMESE"], r["K_RODJDAN"] = "1990", "1", "1"
    r["K_KRSGOD"], r["K_KRSMESE"], r["K_KRSDAN"] = "2000", "2", "2"
    r["K_DETIME"] = dete
    r["K_DETPOL"] = "1"
    r["K_RODIME"] = "Отац"
    r["K_RODPREZ"] = prezime
    r["K_RBRSVE"] = str(rbrsve)
    return [r[c] for c in K_COLS]


def _staging(rows):
    coldefs = ", ".join(f'"{c}" TEXT' for c in K_COLS)
    ph = ", ".join(["%s"] * len(K_COLS))
    with connection.cursor() as cur:
        cur.execute(f"CREATE TEMPORARY TABLE hsp_krstenja ({coldefs})")
        for row in rows:
            cur.execute(f"INSERT INTO hsp_krstenja VALUES ({ph})", row)


class PhantomSvestenikTests(TestCase):
    def setUp(self):
        _clear_caches()

    def test_uid_zero_does_not_create_svestenik(self):
        _staging([_row(1, "Ана", "Петровић", 0)])
        call_command(MigracijaKrstenja(), stdout=StringIO())
        self.assertEqual(Svestenik.objects.count(), 0)
        self.assertIsNone(Krstenje.objects.get().svestenik_id)

    def test_valid_uid_creates_svestenik(self):
        _staging([_row(1, "Ана", "Петровић", 5)])
        call_command(MigracijaKrstenja(), stdout=StringIO())
        self.assertEqual(Svestenik.objects.filter(uid=5).count(), 1)
        self.assertEqual(Krstenje.objects.get().svestenik.uid, 5)
