"""Seed Svestenik rows (priests) in a target tenant.

Constraint: priest = male, age 25-80. Verified by mock.constraints.
"""

from __future__ import annotations

import random as random_module

from django.core.management.base import BaseCommand, CommandError
from registar.mock import constraints
from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Svestenik


class Command(BaseCommand):
    help = "Сеје свештенике у задат tenant."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from",
            dest="source",
            default="mock",
            help="Извор: mock (DBF и fixture још нису).",
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

        if opts["source"] != "mock":
            raise CommandError("seed_svestenici подржава само --from mock тренутно.")

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                n = Svestenik.objects.all().count()
                Svestenik.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Обрисано {n} свештеника у {tenant.schema_name!r}."
                    )
                )

            created = 0
            for _ in range(opts["count"]):
                birthdate = g.rand_birthdate_priest()
                ime = g.rand_first_name("М")  # always male per constraint
                constraints.assert_priest("М", birthdate)
                Svestenik.objects.create(
                    ime=ime,
                    prezime=g.rand_surname(),
                    mesto_rodjenja=g.rand_place(),
                    datum_rodjenja=birthdate,
                    zvanje=random_module.choice(g.ZVANJA_SVESTENIKA),
                )
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Креирано {created} свештеника у {tenant.schema_name!r}."
                )
            )
