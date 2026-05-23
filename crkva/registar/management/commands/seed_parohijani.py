"""Seed Osoba rows in a target tenant.

Currently --from mock only. Other sources land in follow-up commits.
"""

from __future__ import annotations

import random as random_module

from django.core.management.base import BaseCommand, CommandError
from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Osoba


class Command(BaseCommand):
    help = "Сеје парохијане у задат tenant schema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from",
            dest="source",
            default="mock",
            help="Извор: mock | fixture:<path> | dbf",
        )
        parser.add_argument("--tenant", required=True, help="Schema name тенанта.")
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Колико парохијана генерисати (само за mock).",
        )
        parser.add_argument("--seed", type=int, default=None, help="RNG seed.")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="ОПАСНО: брише све постојеће парохијане у тенанту пре уноса.",
        )

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])

        if opts["source"] != "mock":
            raise CommandError(
                f"Извор {opts['source']!r} није имплементиран — тренутно само 'mock'."
            )

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                n = Osoba.objects.all().count()
                Osoba.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(
                        f"Обрисано {n} постојећих парохијана у {tenant.schema_name!r}."
                    )
                )

            created = 0
            for _ in range(opts["count"]):
                pol = g.rand_gender()
                Osoba.objects.create(
                    ime=g.rand_first_name(pol),
                    prezime=g.rand_surname(),
                    pol=pol,
                    datum_rodjenja=g.rand_birthdate_parishioner(),
                    mesto_rodjenja=g.rand_place(),
                    parohijan=True,
                )
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Креирано {created} парохијана у {tenant.schema_name!r}."
                )
            )
