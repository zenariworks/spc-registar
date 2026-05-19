"""Top-level data load orchestrator.

    manage.py load_data --from mock --tenant <schema>   # default count=100
    manage.py load_data --from mock --tenant <schema> --count 200
    manage.py load_data --from mock --tenant <schema> --only seed_parohijani
    manage.py load_data --dry-run

DBF + fixture sources are placeholders; for DBF use the dedicated
`load_dbf` + `importuj_dbf` flow until they\'re unified here.
"""
from __future__ import annotations

import random as random_module

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


# (command, label, supports_count, needs_tenant)
PIPELINE: list[tuple[str, str, bool, bool]] = [
    ("seed_lookups",      "Lookup табеле",      False, False),
    ("seed_parohijani",   "Парохијани",         True,  True),
]


class Command(BaseCommand):
    help = "Орк. за сејање/учитавање ентитета (mock / DBF / fixture)."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", default="mock",
                            help="Извор: mock | dbf-zip:<path> | dbf-dir:<path> | fixture:<path>")
        parser.add_argument("--tenant", default=None,
                            help="Schema name тенанта (обавезно за per-tenant seedere).")
        parser.add_argument("--count", type=int, default=100,
                            help="Број парохијана за mock извор.")
        parser.add_argument("--only", type=str, default=None,
                            help="Само наведени корак(и), зарезом-одвојено.")
        parser.add_argument("--seed", type=int, default=None,
                            help="RNG seed.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Само прикажи редослед, не извршавај.")

    def handle(self, *args, **opts):
        source = opts["source"]
        if source != "mock":
            if source.startswith("dbf-") or source.startswith("fixture:"):
                raise CommandError(
                    f"Извор {source!r} није још имплементиран — за DBF "
                    "користи `load_dbf` па `importuj_dbf`."
                )
            raise CommandError(f"Непознат извор: {source!r}")

        if opts["seed"] is not None:
            random_module.seed(opts["seed"])

        only = opts["only"].split(",") if opts["only"] else None
        steps = [s for s in PIPELINE if not only or s[0] in only]
        if only and not steps:
            raise CommandError(
                f"--only не одговара ниједном кораку. Доступни: "
                f"{', '.join(s[0] for s in PIPELINE)}"
            )

        # Tenant is required only if any selected step needs it
        if any(needs_tenant for _, _, _, needs_tenant in steps) and not opts["tenant"]:
            raise CommandError(
                "--tenant је обавезан за per-tenant seedere "
                "(нпр. seed_parohijani). Користи нпр. "
                "--tenant crkva_sv_petke_cukarica"
            )

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"load_data --from {source}  ({len(steps)} корака, "
            f"tenant={opts['tenant'] or '—'})"
        ))
        for cmd, label, supports_count, needs_tenant in steps:
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"\n→ {label}  (manage.py {cmd})"
            ))
            if opts["dry_run"]:
                self.stdout.write("  (dry-run — прескачем)")
                continue
            kwargs = {"source": source}
            if supports_count:
                kwargs["count"] = opts["count"]
            if needs_tenant:
                kwargs["tenant"] = opts["tenant"]
            if opts["seed"] is not None:
                kwargs["seed"] = opts["seed"]
            call_command(cmd, **kwargs)

        if opts["dry_run"]:
            self.stdout.write(self.style.NOTICE("\nDry-run завршен."))
        else:
            self.stdout.write(self.style.SUCCESS("\nload_data завршен."))
