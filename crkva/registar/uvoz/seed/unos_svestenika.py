"""Seed Svestenik rows (priests) in a target tenant.

Constraint: priest = male, age 25-80. Verified by mock.constraints.
Извори: ``mock`` (реалистични подаци из mock генератора) и ``dummy``
(placeholder редови, наслеђено из некадашње ``unos_svestenika`` команде).
"""

from __future__ import annotations

import random as random_module
from datetime import date

from django.core.management.base import BaseCommand
from registar.mock import constraints
from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Parohija, Svestenik
from registar.models.svestenik import zvanja

IZVORI = ("mock", "dummy")


class Command(BaseCommand):
    help = "Сеје свештенике у задат tenant (mock или dummy подаци)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from",
            dest="source",
            default="mock",
            choices=IZVORI,
            help="Извор података: mock (реалистично) или dummy (placeholder).",
        )
        parser.add_argument("--tenant", required=True, help="Schema name тенанта.")
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Колико свештеника креирати (default 5).",
        )
        parser.add_argument("--seed", type=int, default=None, help="RNG seed.")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="ОПАСНО: брише све свештенике у тенанту пре уноса.",
        )

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                obrisano = Svestenik.objects.all().count()
                Svestenik.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Обрисано {obrisano} свештеника у {tenant.schema_name!r}."
                    )
                )

            if opts["source"] == "dummy":
                self._zasej_dummy(opts["count"])
            else:
                self._zasej_mock(opts["count"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"Креирано {opts['count']} свештеника у {tenant.schema_name!r}."
                )
            )

    def _zasej_mock(self, broj: int) -> None:
        for _ in range(broj):
            datum_rodjenja = g.rand_birthdate_priest()
            constraints.assert_priest("М", datum_rodjenja)
            Svestenik.objects.create(
                ime=g.rand_first_name("М"),
                prezime=g.rand_surname(),
                mesto_rodjenja=g.rand_place(),
                datum_rodjenja=datum_rodjenja,
                zvanje=random_module.choice(g.ZVANJA_SVESTENIKA),
            )

    def _zasej_dummy(self, broj: int) -> None:
        for i in range(broj):
            Svestenik.objects.create(
                ime=f"Ime{i}",
                prezime=f"Prezime{i}",
                mesto_rodjenja=f"Mesto{i}",
                datum_rodjenja=date(1970 + i % 50, (i % 12) + 1, (i % 28) + 1),
                zvanje=random_module.choice(zvanja)[0],
                parohija=Parohija.objects.order_by("?").first(),
            )
