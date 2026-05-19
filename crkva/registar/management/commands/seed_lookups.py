"""Seed reference lookup tables (narodnosti, veroispovesti, ...).

Thin wrapper that runs the existing unos_* seeders in order. Same as
the legacy `unosi` command — renamed for the new seed_* family.
"""
from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand


LOOKUPS = [
    "unos_narodnosti",
    "unos_veroispovesti",
    "unos_zanimanja",
    "unos_slava",
    "unos_eparhija",
]


class Command(BaseCommand):
    help = "Сеје референтне (lookup) табеле."

    def handle(self, *args, **opts):
        for name in LOOKUPS:
            self.stdout.write(self.style.MIGRATE_HEADING(f"  → {name}"))
            call_command(name)
        self.stdout.write(self.style.SUCCESS("Lookup табеле напуњене."))
