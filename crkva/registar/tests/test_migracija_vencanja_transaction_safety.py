"""#329: увоз венчања не сме да пукне нити испразни регистар због једног лошег реда.

Близанац `test_migracija_transaction_safety` за крштења, само за венчања.
``clear_target_table()`` је у истој ``@atomic`` трансакцији као упис, а сваки
ред има savepoint — колизија на ``(godina_registracije, redni_broj)`` прескаче
само тај ред, а неухваћен пад враћа и брисање па стари подаци преживе.
"""

# pylint: disable=missing-function-docstring

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from registar.models import Vencanje
from registar.uvoz.vencanja import SOURCE_COLUMNS
from registar.uvoz.vencanja import Command as MigracijaVencanja


def _staging_row(sifra: int, aktgod: int, z_prezime: str, n_prezime: str) -> list:
    row = {c: "" for c in SOURCE_COLUMNS}
    row["V_SIFRA"] = str(sifra)
    row["V_AKTGOD"] = str(aktgod)
    row["V_Z_IME"], row["V_Z_PREZ"] = "Женик", z_prezime
    row["V_N_IME"], row["V_N_PREZ"] = "Невеста", n_prezime
    row["V_RBRSVEST"] = "0"
    return [row[c] for c in SOURCE_COLUMNS]


class MigracijaVencanjaTransactionSafetyTests(TestCase):
    def setUp(self):
        # Module-level caches survive across tests; clear so stale Osoba/Adresa
        # references from other tests don't leak in.
        from registar.utils.migracija.address import _cache
        from registar.utils.migracija.osoba_repo import _OSOBA_CACHE_BY_SCHEMA

        _cache().clear()
        _OSOBA_CACHE_BY_SCHEMA.clear()

    def _create_staging(self, rows: list[list]) -> None:
        cols = ", ".join(f'"{c}" TEXT' for c in SOURCE_COLUMNS)
        placeholders = ", ".join(["%s"] * len(SOURCE_COLUMNS))
        with connection.cursor() as cur:
            cur.execute(f"CREATE TEMPORARY TABLE hsp_vencanja ({cols})")
            for row in rows:
                cur.execute(f"INSERT INTO hsp_vencanja VALUES ({placeholders})", row)

    def test_duplicate_key_does_not_abort_import(self):
        """Колизија на (godina_registracije, redni_broj) прескаче ред, остали улазе."""
        self._create_staging(
            [
                _staging_row(1, 2000, "Марковић", "Петровић"),
                # Исти (година, редни број) — пада на unique constraint при упису.
                _staging_row(1, 2000, "Јовановић", "Илић"),
                _staging_row(2, 2000, "Николић", "Ђурић"),
            ]
        )
        call_command(MigracijaVencanja(), stdout=StringIO())
        self.assertEqual(Vencanje.objects.count(), 2)
        self.assertEqual(
            set(Vencanje.objects.values_list("redni_broj", flat=True)), {1, 2}
        )

    def test_failed_import_keeps_existing_rows(self):
        """Пад усред увоза враћа и брисање — стари подаци преживљавају."""
        Vencanje.objects.create(godina_registracije=1999, redni_broj=7)
        self._create_staging([_staging_row(1, 2000, "Марковић", "Петровић")])
        with mock.patch(
            "registar.uvoz.vencanja.Command._build_vencanje_data",
            side_effect=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                call_command(MigracijaVencanja(), stdout=StringIO())
        self.assertEqual(Vencanje.objects.count(), 1)
        self.assertTrue(
            Vencanje.objects.filter(godina_registracije=1999, redni_broj=7).exists()
        )
