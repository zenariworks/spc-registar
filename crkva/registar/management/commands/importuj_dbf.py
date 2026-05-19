"""Оркестратор за пуну DBF миграцију.

Покреће целу секвенцу migracija_* + popravi_* + fix_* + mark_* по реду.
Претпоставка: load_dbf је већ напунио staging табеле (hsp_*).

Употреба:
    python manage.py importuj_dbf
    python manage.py importuj_dbf --dry-run
"""
from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


# Run order matters: lookups → core entities → cleanups → calendar fixes.
PIPELINE: list[tuple[str, str]] = [
    ("migracija_slava",               "Slave (фиксне + покретне)"),
    ("migracija_svestenika",          "Свештеници"),
    ("migracija_ukucana_parohijana",  "Домаћинства + парохијани"),
    ("migracija_krstenja",            "Крштења"),
    ("migracija_vencanja",            "Венчања"),
    ("popravi_devojacka",             "Поправка девојачких презимена"),
    ("popravi_duplikate",             "Уклањање дупликата"),
    ("fix_moveable_feasts",           "Корекција покретних празника"),
    ("mark_major_feasts",             "Обележавање црвених слова"),
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

        steps = PIPELINE
        if from_step:
            names = [s[0] for s in PIPELINE]
            if from_step not in names:
                raise CommandError(
                    f"Непознат корак: {from_step}. Доступни: {', '.join(names)}"
                )
            idx = names.index(from_step)
            steps = PIPELINE[idx:]
            self.stdout.write(self.style.WARNING(
                f"Прескакам првих {idx} корак(а), почињем од {from_step}."
            ))

        for i, (cmd, label) in enumerate(steps, start=1):
            heading = f"[{i}/{len(steps)}] {label}  (manage.py {cmd})"
            self.stdout.write(self.style.MIGRATE_HEADING(heading))
            if dry:
                self.stdout.write("  (dry-run — прескачем)")
                continue
            try:
                call_command(cmd)
            except Exception as e:  # pylint: disable=broad-except
                # Halt the pipeline on any error so the user sees where it broke.
                raise CommandError(
                    f"Корак {cmd!r} није успео: {e}\n"
                    f"Поправи проблем и покрени поново са "
                    f"--from-step {cmd}"
                ) from e

        if dry:
            self.stdout.write(self.style.NOTICE("\nDry-run завршен."))
        else:
            self.stdout.write(self.style.SUCCESS("\nДBF пајплајн завршен."))
