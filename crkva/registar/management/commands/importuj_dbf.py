"""Оркестратор за пуну DBF миграцију.

Покреће целу секвенцу migracija_* + popravi_* + fix_* + mark_* по реду.
Претпоставка: load_dbf је већ напунио staging табеле (hsp_*).

Употреба (обавезно преко tenant_command — бира парохијску шему):
    python manage.py tenant_command importuj_dbf --schema=<парохија>
    python manage.py tenant_command importuj_dbf --schema=<парохија> --dry-run
"""

from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from registar.management.commands.popravi_devojacka import Command as PopraviDevojacka
from registar.management.commands.popravi_duplikate import Command as PopraviDuplikate
from registar.seed.unos_slava import Command as UnosSlava
from registar.uvoz.mark_major_feasts import Command as MarkMajorFeasts
from registar.uvoz.migracija_krstenja import Command as MigracijaKrstenja
from registar.uvoz.migracija_svestenika import Command as MigracijaSvestenika
from registar.uvoz.migracija_ukucana_parohijana import (
    Command as MigracijaUkucanaParohijana,
)
from registar.uvoz.migracija_vencanja import Command as MigracijaVencanja

# Run order matters: lookups → core entities → cleanups → calendar fixes.
PIPELINE = [
    ("unos_slava", "Славе (из fixtures/slave.jsonl)", UnosSlava),
    ("migracija_svestenika", "Свештеници", MigracijaSvestenika),
    (
        "migracija_ukucana_parohijana",
        "Домаћинства + парохијани",
        MigracijaUkucanaParohijana,
    ),
    ("migracija_krstenja", "Крштења", MigracijaKrstenja),
    ("migracija_vencanja", "Венчања", MigracijaVencanja),
    ("popravi_devojacka", "Поправка девојачких презимена", PopraviDevojacka),
    ("popravi_duplikate", "Уклањање дупликата", PopraviDuplikate),
    ("mark_major_feasts", "Обележавање црвених слова", MarkMajorFeasts),
]


class Command(BaseCommand):
    help = (
        "Пуни DBF миграциони пајплајн: повезује постојеће команде "
        "migracija_* + popravi_* + fix_* + mark_* у једну операцију."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Само прикажи редослед корака, не извршавај ништа.",
        )
        parser.add_argument(
            "--from-step",
            type=str,
            default=None,
            help=(
                "Настави од одређеног корака (нпр. --from-step migracija_krstenja). "
                "Корисно за поновно покретање после грешке."
            ),
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        from_step = opts["from_step"]

        if connection.schema_name == "public":
            raise CommandError(
                "Одбијено: importuj_dbf се не сме покретати над public шемом — "
                "уписивао би у ПОГРЕШНОГ (или у СВЕ) закупце. Покрени преко "
                "tenant_command: python manage.py tenant_command importuj_dbf "
                "--schema=<парохијска_шема>."
            )

        steps = PIPELINE
        if from_step:
            names = [s[0] for s in PIPELINE]
            if from_step not in names:
                raise CommandError(
                    f"Непознат корак: {from_step}. Доступни: {', '.join(names)}"
                )
            idx = names.index(from_step)
            steps = PIPELINE[idx:]
            self.stdout.write(
                self.style.WARNING(
                    f"Прескакам првих {idx} корак(а), почињем од {from_step}."
                )
            )

        for i, (cmd_id, label, cls) in enumerate(steps, start=1):
            heading = f"[{i}/{len(steps)}] {label}  ({cmd_id})"
            self.stdout.write(self.style.MIGRATE_HEADING(heading))
            if dry:
                self.stdout.write("  (dry-run — прескачем)")
                continue
            try:
                call_command(cls())
            except Exception as e:  # pylint: disable=broad-except
                raise CommandError(
                    f"Корак {cmd_id!r} није успео: {e}\n"
                    f"Поправи проблем и покрени поново са "
                    f"--from-step {cmd_id}"
                ) from e

        if dry:
            self.stdout.write(self.style.NOTICE("\nDry-run завршен."))
        else:
            self.stdout.write(self.style.SUCCESS("\nДBF пајплајн завршен."))
