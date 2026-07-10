"""#329: увоз не сме да пукне нити испразни регистар због једног лошег реда.

``clear_target_table()`` се раније звао изван ``@atomic`` блока, а прва
``IntegrityError`` унутар блока обележава трансакцију као *rollback-only* —
следећи ORM позив баца ``TransactionManagementError`` и команда пуца са већ
обрисаном (и закомитованом) табелом. Сада: брисање је у истој трансакцији
као упис, а сваки ред има savepoint па лош ред не квари остале.
"""

# pylint: disable=missing-function-docstring

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.management.commands.migracija_krstenja import SOURCE_COLUMNS
from registar.models import Krstenje


def _staging_row(sifra: int, aktgod: int, dete_ime: str, otac_prezime: str) -> list:
    row = {c: "" for c in SOURCE_COLUMNS}
    row["K_SIFRA"] = str(sifra)
    row["K_AKTGOD"] = str(aktgod)
    row["K_PROTST"] = "1"
    row["K_RODJGOD"], row["K_RODJMESE"], row["K_RODJDAN"] = "1990", "1", "1"
    row["K_KRSGOD"], row["K_KRSMESE"], row["K_KRSDAN"] = "1990", "2", "2"
    row["K_DETIME"] = dete_ime
    row["K_DETPOL"] = "1"
    row["K_RODIME"] = "Отац"
    row["K_RODPREZ"] = otac_prezime
    row["K_RBRSVE"] = "1"
    return [row[c] for c in SOURCE_COLUMNS]


class MigracijaKrstenjaTransactionSafetyTests(TestCase):
    def setUp(self):
        # Module-level caches survive across tests; clear so stale Osoba/Adresa
        # references from other tests don't leak in.
        from registar.migracija.address import _cache
        from registar.migracija.osoba_repo import _OSOBA_CACHE_BY_SCHEMA

        _cache().clear()
        _OSOBA_CACHE_BY_SCHEMA.clear()

    def _create_staging(self, rows: list[list]) -> None:
        cols = ", ".join(f'"{c}" TEXT' for c in SOURCE_COLUMNS)
        placeholders = ", ".join(["%s"] * len(SOURCE_COLUMNS))
        with connection.cursor() as cur:
            cur.execute(f"CREATE TEMPORARY TABLE hsp_krstenja ({cols})")
            for row in rows:
                cur.execute(f"INSERT INTO hsp_krstenja VALUES ({placeholders})", row)

    def test_duplicate_protocol_number_does_not_abort_import(self):
        """Колизија на krstenje_god_redni_uniq прескаче ред, остали улазе."""
        self._create_staging(
            [
                _staging_row(1, 2000, "Марко", "Марковић"),
                # Исти (година, редни број) кључ, друго дете: пролази dedup,
                # пада на unique constraint при create().
                _staging_row(1, 2000, "Петар", "Петровић"),
                _staging_row(2, 2000, "Јован", "Јовановић"),
            ]
        )
        call_command("migracija_krstenja", stdout=StringIO())
        self.assertEqual(Krstenje.objects.count(), 2)
        self.assertEqual(
            set(Krstenje.objects.values_list("redni_broj", flat=True)), {1, 2}
        )

    def test_failed_import_keeps_existing_rows(self):
        """Пад усред увоза враћа и брисање — стари подаци преживљавају."""
        Krstenje.objects.create(godina_registracije=1999, redni_broj=7, strana=1)
        self._create_staging([_staging_row(1, 2000, "Марко", "Марковић")])
        with mock.patch(
            "registar.management.commands.migracija_krstenja.Command._build_krstenje",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                call_command("migracija_krstenja", stdout=StringIO())
        self.assertEqual(Krstenje.objects.count(), 1)
        self.assertTrue(
            Krstenje.objects.filter(godina_registracije=1999, redni_broj=7).exists()
        )
