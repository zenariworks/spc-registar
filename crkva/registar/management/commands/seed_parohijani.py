"""Seed Parohijan rows in a target tenant.

Parohijan lives in per-tenant schemas (django-tenants). The command
requires --tenant <schema_name> so it knows where to write.

Currently supports --from mock only.
"""
from __future__ import annotations

import random as random_module

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django_tenants.utils import schema_exists

from registar.mock import generators as g
from registar.models import Parohijan
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Сеје парохијане у задат tenant schema."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", default="mock",
                            help="Извор: mock | fixture:<path> | dbf")
        parser.add_argument("--tenant", required=True,
                            help="Schema name тенанта (нпр. crkva_sv_petke_cukarica).")
        parser.add_argument("--count", type=int, default=100,
                            help="Колико парохијана генерисати (само за mock).")
        parser.add_argument("--seed", type=int, default=None,
                            help="RNG seed.")

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])

        tenant_schema = opts["tenant"]
        if not schema_exists(tenant_schema):
            raise CommandError(
                f"Schema {tenant_schema!r} не постоји. Доступни: "
                f"{', '.join(t.schema_name for t in Tenant.objects.all())}"
            )

        tenant = Tenant.objects.get(schema_name=tenant_schema)
        prior = getattr(connection, "tenant", None)
        connection.set_tenant(tenant)
        try:
            source = opts["source"]
            if source == "mock":
                self._seed_from_mock(opts["count"])
            elif source == "dbf":
                raise CommandError("DBF извор иде кроз importuj_dbf, не овде.")
            elif source.startswith("fixture:"):
                raise CommandError("Fixture извор још није имплементиран.")
            else:
                raise CommandError(f"Непознат извор: {source!r}")
        finally:
            if prior is not None:
                connection.set_tenant(prior)
            else:
                connection.set_schema_to_public()

    def _seed_from_mock(self, count: int):
        created = 0
        for _ in range(count):
            gender = g.rand_gender()
            birthdate = g.rand_birthdate_parishioner()
            ime = g.rand_first_name(gender)
            prezime = g.rand_surname()

            Parohijan.objects.create(
                ime=ime,
                prezime=prezime,
                pol=gender,
                datum_rodjenja=birthdate,
                mesto_rodjenja=g.rand_place(),
                parohijan=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Креирано {created} насумичних парохијана у {connection.tenant.schema_name!r}."
        ))
