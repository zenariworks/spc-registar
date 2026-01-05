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

import tempfile
import zipfile
from itertools import batched
from pathlib import Path

from dbfread import DBF
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Django management command to load DBF files into PostgreSQL staging tables."""

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

    BATCH_SIZE = 1000

    def add_arguments(self, parser):
        parser.add_argument(
            "--src_dir",
            type=Path,
            default=None,
            help="Source directory containing .dbf files",
        )
        parser.add_argument(
            "--src_zip",
            type=Path,
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
            self._load_from_directory(Path("/mnt/c/HramSP/dbf"))

    def _load_from_directory(self, src_dir: Path):
        """Load DBF files from a directory."""
        if not src_dir.exists():
            self.stderr.write(
                self.style.ERROR(f"Source directory does not exist: {src_dir}")
            )
            return

        total_loaded = 0
        for dbf_filename, table_name in self.DBF_FILES.items():
            # Try exact match first
            dbf_path = src_dir / dbf_filename

            # Try lowercase if not found
            if not dbf_path.exists():
                dbf_path = src_dir / dbf_filename.lower()

            if not dbf_path.exists():
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

    def _load_from_zip(self, src: Path):
        """Load DBF files from a ZIP archive."""
        if not src.exists():
            self.stderr.write(self.style.ERROR(f"ZIP file does not exist: {src}"))
            return

        total_loaded = 0
        with zipfile.ZipFile(src, "r") as zf:
            # Build a mapping of lowercase names to actual names in the archive
            zip_files = {name.lower(): name for name in zf.namelist()}

            for dbf_filename, table_name in self.DBF_FILES.items():
                # Find the file in the ZIP (case-insensitive)
                # We check if the lowercased filename ends with the lowercased dbf filename
                # to handle potential subdirectories in the ZIP
                target_lower = dbf_filename.lower()
                actual_name = next(
                    (
                        name
                        for lower, name in zip_files.items()
                        if lower.endswith(target_lower)
                    ),
                    None,
                )

                if not actual_name:
                    self.stdout.write(
                        self.style.WARNING(f"DBF file not found in ZIP: {dbf_filename}")
                    )
                    continue

                # Read DBF from ZIP into memory
                dbf_data = zf.read(actual_name)
                count = self._load_dbf_bytes_to_postgres(dbf_data, table_name)
                total_loaded += count
                self.stdout.write(
                    self.style.SUCCESS(f"Loaded {count} rows into {table_name}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal: {total_loaded} rows loaded into staging tables"
            )
        )

    def _load_dbf_to_postgres(self, dbf_path: Path, table_name: str) -> int:
        """Load a single DBF file into a PostgreSQL staging table."""
        # load=False is default, but explicit is better.
        # It means records are streamed from disk.
        table = DBF(dbf_path, encoding="cp1250", load=False)
        return self._load_records_to_postgres(table, table_name)

    def _load_dbf_bytes_to_postgres(self, dbf_bytes: bytes, table_name: str) -> int:
        """Load DBF data from bytes into a PostgreSQL staging table."""
        # We need to write to a temp file since dbfread doesn't support BytesIO directly
        with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
            tmp.write(dbf_bytes)
            tmp_path = Path(tmp.name)

        try:
            table = DBF(tmp_path, encoding="cp1250", load=False)
            return self._load_records_to_postgres(table, table_name)
        finally:
            tmp_path.unlink(missing_ok=True)

    def _load_records_to_postgres(self, table: DBF, table_name: str) -> int:
        """Load DBF records into a PostgreSQL staging table efficiently."""
        columns = table.field_names
        if not columns:
            return 0

        # Prepare SQL for table creation and insertion
        columns_def = ", ".join([f'"{col}" TEXT' for col in columns])
        placeholders = ", ".join(["%s"] * len(columns))
        columns_quoted = ", ".join([f'"{col}"' for col in columns])

        create_sql = f"CREATE TABLE {table_name} ({columns_def})"
        insert_sql = (
            f"INSERT INTO {table_name} ({columns_quoted}) VALUES ({placeholders})"
        )

        total_inserted = 0

        with connection.cursor() as cursor:
            # Drop and recreate the staging table
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(create_sql)

            # Generator to yield formatted rows
            def row_generator():
                for record in table:
                    yield tuple(
                        str(record[col]) if record[col] is not None else None
                        for col in columns
                    )

            # Batch insert using itertools.batched (Python 3.12+)
            for batch in batched(row_generator(), self.BATCH_SIZE):
                cursor.executemany(insert_sql, batch)
                total_inserted += len(batch)

        return total_inserted
