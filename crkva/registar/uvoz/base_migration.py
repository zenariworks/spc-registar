"""Base class for the migracija_* management commands.

Provides:
  - staging-table cleanup
  - target-table reset
  - common --limit / --dry-run / --verbose flags
  - structured logging helpers (log_skip / log_error with RecordContext)
  - bulk-create in batches with progress

Individual migrations stay slim: they declare staging_table + target_model,
parse rows into a dataclass, transform records into model kwargs, and the
base handles batching + commit.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init,too-many-locals,broad-exception-caught,not-callable

from __future__ import annotations

from typing import Iterable

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.transaction import atomic
from registar.migracija.errors import RecordContext, RecordSkipped
from registar.migracija.helpers import rasclani_puno_ime as _rasclani_puno_ime
from registar.migracija.osoba_repo import find_or_create_osoba as _find_osoba
from registar.models import Osoba


class MigrationCommand(BaseCommand):
    """Common scaffolding for migracija_* commands."""

    staging_table: str | None = None
    target_model = None

    # Common CLI flags
    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Обради само првих N записа (0 = све, дефолт).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Не уписује у базу; само симулира.",
        )
        parser.add_argument(
            "--verbose-errors",
            action="store_true",
            help="Прикажи cео контекст за сваку грешку или прескок.",
        )

    # --- Safety guard ---

    def zabrani_nad_public(self) -> None:
        """Одбиј рад над public шемом (#330).

        migracija_* пишу у per-tenant табеле; над public-ом или нема
        табела или се пише у погрешну шему. Покретати преко
        ``tenant_command <cmd> --schema=<парохија>``.
        """
        if connection.schema_name == "public":
            raise CommandError(
                f"Одбијено: {self.__class__.__module__.rsplit('.', 1)[-1]} "
                "над public шемом. Покрени преко tenant_command "
                "(--schema бира парохију)."
            )

    # --- Staging / target setup ---

    def drop_staging_table(self) -> None:
        if not (table := self.staging_table):
            raise NotImplementedError("staging_table мора бити дефинисан у подкласи")
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        self.stdout.write(self.style.SUCCESS(f"Обрисана staging табела '{table}'."))

    def clear_target_table(self) -> None:
        if not self.target_model:
            raise NotImplementedError("target_model мора бити дефинисан у подкласи")
        self.target_model.objects.all().delete()

    # --- Logging ---

    def log_success(self, count: int, table_name: str | None = None) -> None:
        name = table_name or (
            self.target_model._meta.verbose_name_plural
            if self.target_model
            else "записа"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела '{name}': {count} нових уноса."
            )
        )

    def log_error(self, ctx_or_msg, message: str | None = None) -> None:
        """Log an error. Accepts either a string or (RecordContext, message)."""
        if isinstance(ctx_or_msg, RecordContext):
            self.stdout.write(self.style.ERROR(f"Грешка [{ctx_or_msg}]: {message}"))
        else:
            self.stdout.write(self.style.ERROR(f"Грешка: {ctx_or_msg}"))

    def log_warning(self, message: str) -> None:
        self.stdout.write(self.style.WARNING(message))

    def log_skip(self, ctx_or_reason, reason: str | None = None) -> None:
        if isinstance(ctx_or_reason, RecordContext):
            self.stdout.write(
                self.style.WARNING(f"Прескочено [{ctx_or_reason}]: {reason}")
            )
        else:
            self.stdout.write(self.style.WARNING(f"Прескочено: {ctx_or_reason}"))

    # --- Helpers (delegating to the migracija package) ---

    def rasclani_puno_ime(self, puno_ime: str | None):
        return _rasclani_puno_ime(puno_ime)

    def get_or_create_osoba(self, ime, prezime, **dodatno) -> Osoba | None:
        return _find_osoba(ime, prezime, **dodatno)

    # --- Bulk insert ---

    @atomic
    def migrate_in_batches(
        self,
        records: Iterable[dict | None],
        batch_size: int = 500,
        dry_run: bool = False,
    ) -> int:
        batch: list = []
        created_count = 0

        def _upisi(redovi: list) -> None:
            nonlocal created_count
            if not redovi:
                return
            if dry_run:
                created_count += len(redovi)  # процена (ништа се не уписује)
                return
            # ignore_conflicts=True: прескочени (конфликтни) редови на Postgres
            # немају PK; бројимо само стварно уметнуте да „created" не буде
            # прецењен (#340).
            upisani = self.target_model.objects.bulk_create(
                redovi, ignore_conflicts=True
            )
            created_count += sum(1 for o in upisani if o.pk is not None)

        for idx, data in enumerate(records, start=1):
            if data is None:
                continue
            batch.append(self.target_model(**data))

            if len(batch) >= batch_size:
                _upisi(batch)
                batch = []
                self.stdout.write(f"Обрађено {idx} записа...")

        _upisi(batch)
        return created_count

    # --- Iteration helper for refactored migrations ---

    @staticmethod
    def take(iterable, n: int):
        """Return up to N items from an iterable (or all if n==0)."""
        if n <= 0:
            yield from iterable
            return
        for i, item in enumerate(iterable):
            if i >= n:
                return
            yield item


# Re-export for backwards compatibility with old imports
__all__ = ["MigrationCommand", "RecordContext", "RecordSkipped"]
