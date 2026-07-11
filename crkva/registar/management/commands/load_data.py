"""Top-level data load orchestrator (mock / DBF / fixture)."""

from __future__ import annotations

import random as random_module

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from registar.management.commands import (
    unos_adresa,
    unos_domacinstava,
    unos_krstenja,
    unos_parohijana,
    unos_sifarnika,
    unos_svestenika,
    unos_vencanja,
)


class Step:
    def __init__(
        self,
        modul,
        label,
        *,
        takes_source=True,
        takes_count=True,
        takes_tenant=True,
        takes_seed=True,
        takes_reset=True,
        default_count=None,
        divisor=1,
    ):
        self.name = modul.__name__.rsplit(".", 1)[-1]
        self.modul = modul
        self.label = label
        self.takes_source = takes_source
        self.takes_count = takes_count
        self.takes_tenant = takes_tenant
        self.takes_seed = takes_seed
        self.takes_reset = takes_reset
        self.default_count = default_count
        self.divisor = divisor


PIPELINE: list[Step] = [
    Step(
        unos_sifarnika,
        "Lookup табеле",
        takes_source=False,
        takes_count=False,
        takes_seed=False,
        takes_reset=False,
    ),
    Step(unos_adresa, "Адресе", default_count=30, divisor=3),
    Step(unos_svestenika, "Свештеници", default_count=5, divisor=20),
    Step(unos_parohijana, "Парохијани", default_count=100, divisor=1),
    Step(unos_domacinstava, "Домаћинства", default_count=33, divisor=3),
    Step(unos_krstenja, "Крштења", default_count=25, divisor=4),
    Step(unos_vencanja, "Венчања", default_count=10, divisor=10),
]


class Command(BaseCommand):
    help = "Орк. за сејање/учитавање ентитета (mock / DBF / fixture)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from",
            dest="source",
            default="mock",
            help="Извор: mock | dbf-zip:<path> | dbf-dir:<path> | fixture:<path>",
        )
        parser.add_argument(
            "--tenant",
            default=None,
            help="Schema name тенанта (обавезно за per-tenant seedere).",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=None,
            help="Базни број (parohijani). Остали се скалирају.",
        )
        parser.add_argument(
            "--only",
            type=str,
            default=None,
            help="Само наведени корак(и), зарезом-одвојено.",
        )
        parser.add_argument("--seed", type=int, default=None, help="RNG seed.")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="ОПАСНО: брише постојеће редове пре сваког корака.",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Само прикажи редослед."
        )

    def handle(self, *args, **opts):
        source = opts["source"]
        if source != "mock":
            if source.startswith("dbf-") or source.startswith("fixture:"):
                raise CommandError(
                    f"Извор {source!r} још није имплементиран — за DBF "
                    "користи `load_dbf` па `importuj_dbf`."
                )
            raise CommandError(f"Непознат извор: {source!r}")

        if opts["seed"] is not None:
            random_module.seed(opts["seed"])

        only = opts["only"].split(",") if opts["only"] else None
        steps = [s for s in PIPELINE if not only or s.name in only]
        if only and not steps:
            raise CommandError(
                f"--only не одговара ниједном кораку. Доступни: "
                f"{', '.join(s.name for s in PIPELINE)}"
            )

        if any(s.takes_tenant for s in steps) and not opts["tenant"]:
            raise CommandError(
                "--tenant је обавезан за per-tenant seedere. "
                "Пример: --tenant crkva_sv_nikole_zaandam"
            )

        base_count = opts["count"]

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"load_data --from {source}  ({len(steps)} корака, "
                f"tenant={opts['tenant'] or '—'}, reset={opts['reset']})"
            )
        )

        for step in steps:
            self.stdout.write(
                self.style.MIGRATE_HEADING(f"\n→ {step.label}  (manage.py {step.name})")
            )
            if opts["dry_run"]:
                self.stdout.write("  (dry-run — прескачем)")
                continue

            kwargs = {}
            if step.takes_source:
                kwargs["source"] = source
            if step.takes_tenant:
                kwargs["tenant"] = opts["tenant"]
            if step.takes_count:
                if base_count is not None:
                    kwargs["count"] = max(1, base_count // step.divisor)
                else:
                    kwargs["count"] = step.default_count
            if step.takes_seed and opts["seed"] is not None:
                kwargs["seed"] = opts["seed"]
            if step.takes_reset and opts["reset"]:
                kwargs["reset"] = True

            call_command(step.name, **kwargs)

        if opts["dry_run"]:
            self.stdout.write(self.style.NOTICE("\nDry-run завршен."))
        else:
            self.stdout.write(self.style.SUCCESS("\nload_data завршен."))
