"""Оркестратор учитавања података: mock сејање, DBF увоз или fixture."""

from __future__ import annotations

import random as random_module
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from registar.mock.tenant_ctx import with_tenant
from registar.uvoz.seed import (
    unos_adresa,
    unos_domacinstava,
    unos_krstenja,
    unos_parohijana,
    unos_sifarnika,
    unos_svestenika,
    unos_vencanja,
)


@dataclass(frozen=True)
class Step:
    """Један корак mock сејања и аргументи које његова команда прима.

    `default_count` важи без `--count`; са њим корак добија
    `--count // divisor`, а најмање 1.
    """

    modul: ModuleType
    oznaka: str
    takes_source: bool = True
    takes_count: bool = True
    takes_tenant: bool = True
    takes_seed: bool = True
    takes_reset: bool = True
    default_count: int | None = None
    divisor: int = 1

    @property
    def naziv(self) -> str:
        """Назив команде корака (последњи део имена модула)."""
        return self.modul.__name__.rsplit(".", 1)[-1]

    def kwargs(self, opts: dict) -> dict:
        """Аргументи за команду корака из опција `load_data`."""
        kwargs = {}
        if self.takes_source:
            kwargs["source"] = "mock"
        if self.takes_tenant:
            kwargs["tenant"] = opts["tenant"]
        if self.takes_count:
            kwargs["count"] = self._count(opts["count"])
        if self.takes_seed and opts["seed"] is not None:
            kwargs["seed"] = opts["seed"]
        if self.takes_reset and opts["reset"]:
            kwargs["reset"] = True
        return kwargs

    def _count(self, base_count: int | None) -> int | None:
        """Број записа: подразумевани, или базни број скалиран делиоцем."""
        if base_count is None:
            return self.default_count
        return max(1, base_count // self.divisor)


PIPELINE: list[Step] = [
    Step(
        unos_sifarnika,
        "Шифрарник",
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


def izaberi_korake(only: str | None) -> list[Step]:
    """Кораци из `--only` (зарезом одвојени називи), или сви без њега."""
    if not only:
        return list(PIPELINE)
    nazivi = only.split(",")
    koraci = [s for s in PIPELINE if s.naziv in nazivi]
    if not koraci:
        raise CommandError(
            f"--only не одговара ниједном кораку. Доступни: "
            f"{', '.join(s.naziv for s in PIPELINE)}"
        )
    return koraci


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
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])

        if source == "mock":
            self._zasej_mock(opts)
        elif source.startswith("dbf-zip:") or source.startswith("dbf-dir:"):
            self._migriraj_dbf(source, opts)
        elif source.startswith("fixture:"):
            raise CommandError(f"Извор {source!r} још није имплементиран.")
        else:
            raise CommandError(f"Непознат извор: {source!r}")

    def _zasej_mock(self, opts) -> None:
        """Покреће изабране кораке сејања редом (или их само наводи уз --dry-run)."""
        koraci = izaberi_korake(opts["only"])
        if any(s.takes_tenant for s in koraci) and not opts["tenant"]:
            raise CommandError(
                "--tenant је обавезан за per-tenant seedere. "
                "Пример: --tenant crkva_sv_nikole_zaandam"
            )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"load_data --from mock  ({len(koraci)} корака, "
                f"tenant={opts['tenant'] or '—'}, reset={opts['reset']})"
            )
        )
        for korak in koraci:
            self._pokreni_korak(korak, opts)

        if opts["dry_run"]:
            self.stdout.write(self.style.NOTICE("\nDry-run завршен."))
        else:
            self.stdout.write(self.style.SUCCESS("\nload_data завршен."))

    def _pokreni_korak(self, korak: Step, opts) -> None:
        """Наслов корака, па позив његове команде (осим уз --dry-run)."""
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"\n→ {korak.oznaka}  (manage.py {korak.naziv})")
        )
        if opts["dry_run"]:
            self.stdout.write("  (dry-run — прескачем)")
            return
        call_command(korak.modul.Command(), **korak.kwargs(opts))

    def _migriraj_dbf(self, source: str, opts) -> None:
        """DBF увоз под шемом закупца: load_dbf → unos_sifarnika → importuj_dbf."""
        if not opts["tenant"]:
            raise CommandError("--tenant је обавезан за DBF увоз.")

        prefiks, _, putanja = source.partition(":")
        putanja = putanja.strip()
        if not putanja:
            raise CommandError(f"Недостаје путања у извору {source!r}.")

        izvor = Path(putanja)
        if not izvor.exists():
            raise CommandError(f"DBF извор не постоји: {izvor}")

        load_kwargs = {"src_zip": izvor} if prefiks == "dbf-zip" else {"src_dir": izvor}

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"load_data --from {source}  (tenant={opts['tenant']})"
            )
        )
        if opts["dry_run"]:
            self.stdout.write(
                f"  (dry-run) load_dbf({putanja}) → unos_sifarnika → importuj_dbf над "
                f"{opts['tenant']!r}"
            )
            return

        with with_tenant(opts["tenant"]):
            self.stdout.write(self.style.MIGRATE_HEADING("\n→ load_dbf"))
            call_command("load_dbf", **load_kwargs)
            self.stdout.write(self.style.MIGRATE_HEADING("\n→ unos_sifarnika"))
            call_command(unos_sifarnika.Command(), tenant=opts["tenant"])
            self.stdout.write(self.style.MIGRATE_HEADING("\n→ importuj_dbf"))
            call_command("importuj_dbf")

        self.stdout.write(self.style.SUCCESS("\nload_data (DBF) завршен."))
