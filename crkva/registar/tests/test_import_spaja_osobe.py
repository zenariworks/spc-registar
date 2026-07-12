"""#332: увоз не сме да споји различите људе по имену.

Регистарски принципи (дете у крштењу; женик и невеста у венчању) су по
природи нове особе. Раније их је ``nadji_dodaj_osobu`` дедуплицирао по
(ime, prezime), па су се два различита „Никола Петровић“ детета спајала, а
невеста (креирана под МЛАДОЖЕЊИНИМ презименом) спајала са свекрвом.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.models import Krstenje, Osoba, Vencanje
from registar.uvoz.migracija_krstenja import SOURCE_COLUMNS as K_COLS
from registar.uvoz.migracija_krstenja import Command as MigracijaKrstenja
from registar.uvoz.migracija_vencanja import SOURCE_COLUMNS as V_COLS
from registar.uvoz.migracija_vencanja import Command as MigracijaVencanja


def _clear_caches():
    from registar.migracija.address import _cache
    from registar.migracija.osoba_repo import _OSOBA_CACHE_BY_SCHEMA

    _cache().clear()
    _OSOBA_CACHE_BY_SCHEMA.clear()


def _krstenje_row(sifra, aktgod, dete_ime, otac_prezime, rodj_god, strana=1):
    row = {c: "" for c in K_COLS}
    row["K_SIFRA"] = str(sifra)
    row["K_AKTGOD"] = str(aktgod)
    row["K_PROTST"] = str(strana)
    row["K_RODJGOD"], row["K_RODJMESE"], row["K_RODJDAN"] = str(rodj_god), "1", "1"
    row["K_KRSGOD"], row["K_KRSMESE"], row["K_KRSDAN"] = str(aktgod), "2", "2"
    row["K_DETIME"] = dete_ime
    row["K_DETPOL"] = "1"
    row["K_RODIME"] = "Отац"
    row["K_RODPREZ"] = otac_prezime
    row["K_RBRSVE"] = "1"
    return [row[c] for c in K_COLS]


def _vencanje_row(sifra, aktgod, z_ime, z_prez, n_ime, n_prez):
    row = {c: "" for c in V_COLS}
    row["V_SIFRA"] = str(sifra)
    row["V_AKTGOD"] = str(aktgod)
    row["V_GODINA"], row["V_MESEC"], row["V_DAN"] = str(aktgod), "6", "15"
    row["V_Z_IME"], row["V_Z_PREZ"] = z_ime, z_prez
    row["V_N_IME"], row["V_N_PREZ"] = n_ime, n_prez
    return [row[c] for c in V_COLS]


def _make_staging(table, cols, rows):
    coldefs = ", ".join(f'"{c}" TEXT' for c in cols)
    ph = ", ".join(["%s"] * len(cols))
    with connection.cursor() as cur:
        cur.execute(f"CREATE TEMPORARY TABLE {table} ({coldefs})")
        for row in rows:
            cur.execute(f"INSERT INTO {table} VALUES ({ph})", row)


class KrstenjeDistinctChildrenTests(TestCase):
    def setUp(self):
        _clear_caches()

    def test_two_same_name_children_are_distinct_people(self):
        _make_staging(
            "hsp_krstenja",
            K_COLS,
            [
                _krstenje_row(1, 2000, "Никола", "Петровић", 1990),
                _krstenje_row(2, 2000, "Никола", "Петровић", 1995, strana=2),
            ],
        )
        call_command(MigracijaKrstenja(), stdout=StringIO())

        self.assertEqual(Krstenje.objects.count(), 2)
        deca = list(Krstenje.objects.order_by("redni_broj").select_related("dete"))
        self.assertNotEqual(
            deca[0].dete_id,
            deca[1].dete_id,
            "два различита детета истог имена не смеју да деле једну Osoba",
        )
        godine = {k.dete.datum_rodjenja.year for k in deca}
        self.assertEqual(godine, {1990, 1995})


class VencanjeBrideNotMergedTests(TestCase):
    def setUp(self):
        _clear_caches()

    def test_bride_not_merged_with_grooms_mother(self):
        # Groom's mother already in the registry under the family surname.
        svekrva = Osoba.objects.create(ime="Мара", prezime="Петровић")

        _make_staging(
            "hsp_vencanja",
            V_COLS,
            # Bride "Мара" (devojacko "Јовановић") marries a Петровић → married
            # surname becomes Петровић, colliding by name with the mother.
            [_vencanje_row(1, 2000, "Петар", "Петровић", "Мара", "Јовановић")],
        )
        call_command(MigracijaVencanja(), stdout=StringIO())

        self.assertEqual(Vencanje.objects.count(), 1)
        venc = Vencanje.objects.get()
        self.assertIsNotNone(venc.nevesta_id)
        self.assertNotEqual(
            venc.nevesta_id, svekrva.pk, "невеста не сме да буде свекрва"
        )
        # Two distinct "Мара Петровић" now: the mother + the bride.
        self.assertEqual(
            Osoba.objects.filter(ime="Мара", prezime="Петровић").count(), 2
        )
        # The mother's record is untouched (no devojacko surname written to her).
        svekrva.refresh_from_db()
        self.assertFalse(svekrva.devojacko)
        # The bride keeps her own devojacko surname.
        self.assertEqual(venc.nevesta.devojacko, "Јовановић")
