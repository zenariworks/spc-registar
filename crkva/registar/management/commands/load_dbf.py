"""
Load DBF files directly into PostgreSQL staging tables.

This command reads legacy DBF files from the old church application (HramSP)
and loads them into staging tables in PostgreSQL. The staging tables use the
'hsp_' prefix (e.g., hsp_domacini, hsp_krstenja, etc.).

Supports reading from:
- A directory containing DBF files
- A ZIP archive containing DBF files

Usage:
    # From directory
    python manage.py load_dbf --src_dir /path/to/dbf

    # From ZIP file
    python manage.py load_dbf --src_zip /path/to/crkva.zip
"""

import os
import zipfile

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
            default=None,
            help="Source directory containing .dbf files",
        )
        parser.add_argument(
            "--src_zip",
            type=str,
            default=None,
            help="Source ZIP file containing .dbf files",
        )

    def handle(self, *args, **options):
        src_dir = options["src_dir"]
        src_zip = options["src_zip"]

        if src_zip:
            self._load_from_zip(src_zip)
        elif src_dir:
            self._load_from_directory(src_dir)
        else:
            # Default to directory if neither specified
            self._load_from_directory("/mnt/c/HramSP/dbf")

    def _load_from_directory(self, src_dir):
        """Load DBF files from a directory."""
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

    def _load_from_zip(self, src_zip):
        """Load DBF files from a ZIP archive."""
        if not os.path.exists(src_zip):
            self.stdout.write(self.style.ERROR(f"ZIP file does not exist: {src_zip}"))
            return

        total_loaded = 0
        with zipfile.ZipFile(src_zip, "r") as zf:
            # Build a mapping of lowercase names to actual names in the archive
            zip_files = {name.lower(): name for name in zf.namelist()}

            for dbf_filename, table_name in self.DBF_FILES.items():
                # Find the file in the ZIP (case-insensitive, may be in subdirectory)
                actual_name = None
                for zip_path_lower, zip_path in zip_files.items():
                    if zip_path_lower.endswith(dbf_filename.lower()):
                        actual_name = zip_path
                        break

                if not actual_name:
                    self.stdout.write(
                        self.style.WARNING(f"DBF file not found in ZIP: {dbf_filename}")
                    )
                    continue

                # Read DBF from ZIP into memory
                dbf_data = zf.read(actual_name)
                count = self._load_dbf_bytes_to_postgres(
                    dbf_data, table_name, dbf_filename
                )
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
        return self._load_records_to_postgres(list(dbf_data), table_name)

    def _load_dbf_bytes_to_postgres(self, dbf_bytes, table_name, filename):
        """Load DBF data from bytes into a PostgreSQL staging table."""
        # DBF class can read from a file-like object using FieldParser
        # We need to write to a temp file since dbfread doesn't support BytesIO directly
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
            tmp.write(dbf_bytes)
            tmp_path = tmp.name

        try:
            dbf_data = DBF(tmp_path, encoding="cp1250")
            return self._load_records_to_postgres(list(dbf_data), table_name)
        finally:
            os.unlink(tmp_path)

    def _load_records_to_postgres(self, records, table_name):
        """Load a list of DBF records into a PostgreSQL staging table."""
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
