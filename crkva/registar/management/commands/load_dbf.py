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
from pathlib import Path
from typing import Iterator, Sequence

from dbfread import DBF
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Load DBF files into PostgreSQL staging tables"

    DBF_MAPPING = {
        "HSPDOMACINI.DBF": "hsp_domacini",
        "HSPKRST.DBF": "hsp_krstenja",
        "HSPSLAVE.DBF": "hsp_slave",
        "HSPSVEST.DBF": "hsp_svestenici",
        "HSPUKUCANI.DBF": "hsp_ukucani",
        "HSPULICE.DBF": "hsp_ulice",
        "HSPVENC.DBF": "hsp_vencanja",
    }

    BATCH_SIZE = 1000
    DEFAULT_SOURCE = Path("/mnt/c/HramSP/dbf")

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--src_dir",
            type=Path,
            help="Source directory containing .dbf files",
        )
        group.add_argument(
            "--src_zip",
            type=Path,
            help="Source ZIP file containing .dbf files",
        )

    def handle(self, *args, **options):
        src_dir = options["src_dir"]
        src_zip = options["src_zip"]

        source = src_zip or src_dir or self.DEFAULT_SOURCE

        if src_zip:
            loader = self.load_from_zip
        elif src_dir or source.is_dir():
            loader = self.load_from_directory
        else:
            self.stderr.write(self.style.ERROR(f"Invalid source: {source}"))
            return

        total_loaded = loader(source)
        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal: {total_loaded} rows loaded into staging tables"
            )
        )

    def load_from_directory(self, src_dir: Path) -> int:
        if not src_dir.exists():
            self.stderr.write(self.style.ERROR(f"Directory not found: {src_dir}"))
            return 0

        return self._process_files(
            (src_dir / expected for expected in self.DBF_MAPPING),
            self.DBF_MAPPING.values(),
        )

    def load_from_zip(self, src_zip: Path) -> int:
        if not src_zip.exists():
            self.stderr.write(self.style.ERROR(f"ZIP file not found: {src_zip}"))
            return 0

        total = 0
        with zipfile.ZipFile(src_zip) as zf:
            zip_contents = {Path(name).name.lower(): name for name in zf.namelist()}

            for expected_filename, table_name in self.DBF_MAPPING.items():
                expected_lower = expected_filename.lower()
                archive_name = zip_contents.get(expected_lower)

                if not archive_name:
                    self.stdout.write(
                        self.style.WARNING(f"Not found in ZIP: {expected_filename}")
                    )
                    continue

                with zf.open(archive_name) as dbf_file:
                    with tempfile.NamedTemporaryFile(
                        suffix=".dbf", delete=False
                    ) as tmp:
                        tmp.write(dbf_file.read())
                        tmp_path = Path(tmp.name)

                    try:
                        count = self._load_dbf_file(tmp_path, table_name)
                    finally:
                        tmp_path.unlink(missing_ok=True)

                    total += count
                    self.stdout.write(
                        self.style.SUCCESS(f"Loaded {count} rows into {table_name}")
                    )

        return total

    def _process_files(self, paths: Iterator[Path], table_names: Sequence[str]) -> int:
        total = 0
        for path, table_name in zip(paths, table_names):
            candidates = list(path.parent.glob(f"{path.name}*"))  # case-insensitive-ish
            if not candidates:
                self.stdout.write(
                    self.style.WARNING(f"DBF file not found: {path.name}")
                )
                continue

            # Pick first match (prefer exact case, then any)
            dbf_path = next(
                (p for p in candidates if p.name.lower() == path.name.lower()),
                candidates[0],
            )

            count = self._load_dbf_file(dbf_path, table_name)
            total += count
            self.stdout.write(
                self.style.SUCCESS(f"Loaded {count} rows into {table_name}")
            )

        return total

    def _load_dbf_file(self, dbf_path: Path, table_name: str) -> int:
        try:
            table = DBF(str(dbf_path), encoding="cp1250", load=False)
            return self._load_records(table, table_name)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to read {dbf_path.name}: {e}"))
            return 0

    def _load_records(self, table: DBF, table_name: str) -> int:
        columns = table.field_names
        if not columns:
            return 0

        column_defs = ", ".join(f'"{col}" TEXT' for col in columns)
        column_list = ", ".join(f'"{col}"' for col in columns)
        placeholders = ", ".join("%s" for _ in columns)

        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
        insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"

        total_inserted = 0

        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(create_sql)

            def rows():
                for record in table:
                    yield tuple(
                        None if value is None else str(value)
                        for value in record.values()
                    )

            batch = []
            for row in rows():
                batch.append(row)
                if len(batch) >= self.BATCH_SIZE:
                    cursor.executemany(insert_sql, batch)
                    total_inserted += len(batch)
                    batch.clear()

            if batch:
                cursor.executemany(insert_sql, batch)
                total_inserted += len(batch)

        return total_inserted
