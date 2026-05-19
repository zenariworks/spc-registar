"""Seed Adresa rows in a target tenant."""
from __future__ import annotations

import random as random_module

from django.core.management.base import BaseCommand, CommandError

from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Adresa


class Command(BaseCommand):
    help = "Сеје адресе у задат tenant."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", default="mock")
        parser.add_argument("--tenant", required=True, help="Schema name тенанта.")
        parser.add_argument("--count", type=int, default=30,
                            help="Колико адреса креирати (default 30 — ~1 адреса на ~3 парохијана).")
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--reset", action="store_true",
                            help="ОПАСНО: брише све адресе у тенанту пре уноса.")

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])

        if opts["source"] != "mock":
            raise CommandError("seed_adrese подржава само --from mock тренутно.")

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                n = Adresa.objects.all().count()
                Adresa.objects.all().delete()
                self.stdout.write(self.style.WARNING(
                    f"Обрисано {n} адреса у {tenant.schema_name!r}."
                ))

            created = 0
            for _ in range(opts["count"]):
                Adresa.objects.create(
                    ulica=g.rand_street(),
                    broj=str(random_module.randint(1, 250)),
                    mesto=g.rand_place(),
                    postkod=g.rand_postcode(),
                )
                created += 1

            self.stdout.write(self.style.SUCCESS(
                f"Креирано {created} адреса у {tenant.schema_name!r}."
            ))
