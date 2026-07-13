"""#340: увоз крштења не сме да прави фантомског свештеника.

``migracija_krstenja`` је радила ``get_or_create(uid=svestenik_id)`` за сваки
ред, па су настајали празни ``Svestenik`` редови (``__str__`` = „  ") који
искачу у select2 — не само за ``K_RBRSVE`` = 0 него за сваки непостојећи id.
Сада се крштење везује само за већ увезеног свештеника (као ``vencanja``);
непознат id остаје ``None``, никад не прави празан ред.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.models import Krstenje, Svestenik
from registar.uvoz.krstenja import SOURCE_COLUMNS as K_COLS
from registar.uvoz.krstenja import Command as MigracijaKrstenja


def _clear_caches():
    from registar.utils.migracija.address import _cache
    from registar.utils.migracija.osoba_repo import _OSOBA_CACHE_BY_SCHEMA

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

    def test_known_uid_links_existing_svestenik(self):
        # Свештеник већ увезен (`svestenici` иде пре `krstenja`) → веза, без новог реда.
        Svestenik.objects.create(uid=5, ime="Марко", prezime="Марковић", zvanje="јереј")
        _staging([_row(1, "Ана", "Петровић", 5)])
        call_command(MigracijaKrstenja(), stdout=StringIO())
        self.assertEqual(Svestenik.objects.count(), 1)
        self.assertEqual(Krstenje.objects.get().svestenik.uid, 5)

    def test_unknown_uid_does_not_create_svestenik(self):
        # Непостојећи свештеник → крштење остаје без свештеника, нема празног реда.
        _staging([_row(1, "Ана", "Петровић", 7)])
        call_command(MigracijaKrstenja(), stdout=StringIO())
        self.assertEqual(Svestenik.objects.count(), 0)
        self.assertIsNone(Krstenje.objects.get().svestenik_id)
