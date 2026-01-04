"""
Load DBF files directly into PostgreSQL staging tables.

This command reads legacy DBF files from the old church application (HramSP)
and loads them into staging tables in PostgreSQL. The staging tables use the
'hsp_' prefix (e.g., hsp_domacini, hsp_krstenja, etc.).

Usage:
    docker compose run --rm app sh -c "python manage.py load_dbf --src_dir /path/to/dbf"
"""

import os

from dbfread import DBF
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Load DBF files into PostgreSQL staging tables"

    # Mapping of DBF files to staging table names
    DBF_FILES = {
        "HSPDOMACINI.DBF": "hsp_domacini",
        "HSPKRST.DBF": "hsp_krstenja",
        "HSPSLAVE.DBF": "hsp_slave",
        "HSPSVEST.DBF": "hsp_svestenici",
        "HSPUKUCANI.DBF": "hsp_ukucani",
        "HSPULICE.DBF": "hsp_ulice",
        "HSPVENC.DBF": "hsp_vencanja",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--src_dir",
            type=str,
            default="/mnt/c/HramSP/dbf",
            help="Source directory containing .dbf files",
        )

    def handle(self, *args, **options):
        src_dir = options["src_dir"]

        if not os.path.exists(src_dir):
            self.stdout.write(
                self.style.ERROR(f"Source directory does not exist: {src_dir}")
            )
            return

        total_loaded = 0
        for dbf_filename, table_name in self.DBF_FILES.items():
            dbf_path = os.path.join(src_dir, dbf_filename)

            # Try both uppercase and lowercase
            if not os.path.exists(dbf_path):
                dbf_path = os.path.join(src_dir, dbf_filename.lower())

            if not os.path.exists(dbf_path):
                self.stdout.write(
                    self.style.WARNING(f"DBF file not found: {dbf_filename}")
                )
                continue

            count = self._load_dbf_to_postgres(dbf_path, table_name)
            total_loaded += count
            self.stdout.write(
                self.style.SUCCESS(f"Loaded {count} rows into {table_name}")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal: {total_loaded} rows loaded into staging tables"
            )
        )

    def _load_dbf_to_postgres(self, dbf_path, table_name):
        """Load a single DBF file into a PostgreSQL staging table."""
        dbf_data = DBF(dbf_path, encoding="cp1250")
        records = list(dbf_data)

        if not records:
            return 0

        # Get column names from first record
        columns = list(records[0].keys())

        with connection.cursor() as cursor:
            # Drop and recreate the staging table
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            # Create table with all columns as TEXT (simple staging approach)
            columns_def = ", ".join([f'"{col}" TEXT' for col in columns])
            cursor.execute(f"CREATE TABLE {table_name} ({columns_def})")

            # Insert all records
            placeholders = ", ".join(["%s"] * len(columns))
            columns_quoted = ", ".join([f'"{col}"' for col in columns])
            insert_sql = (
                f"INSERT INTO {table_name} ({columns_quoted}) VALUES ({placeholders})"
            )

            for record in records:
                values = [
                    str(record[col]) if record[col] is not None else None
                    for col in columns
                ]
                cursor.execute(insert_sql, values)

        return len(records)
