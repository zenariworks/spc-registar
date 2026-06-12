"""Seed reference lookup tables (narodnosti, veroispovesti, ...).

Wraps the legacy unos_* commands. Lookup data lives in per-tenant schemas
(registar is in TENANT_APPS), so --tenant is required.
"""

from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand
from registar.mock.tenant_ctx import with_tenant

LOOKUPS = [
    "unos_narodnosti",
    "unos_veroispovesti",
    "unos_zanimanja",
    "unos_slava",
    "unos_eparhija",
]


class Command(BaseCommand):
    help = "Сеје референтне (lookup) табеле у задат tenant."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Schema name тенанта.")

    def handle(self, *args, **opts):
        with with_tenant(opts["tenant"]) as tenant:
            for name in LOOKUPS:
                self.stdout.write(self.style.MIGRATE_HEADING(f"  → {name}"))
                call_command(name)
            self.stdout.write(
                self.style.SUCCESS(f"Lookup табеле напуњене у {tenant.schema_name!r}.")
            )
