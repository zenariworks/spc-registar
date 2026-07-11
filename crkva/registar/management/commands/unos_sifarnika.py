"""Seed reference lookup tables into a target tenant.

Равни шифарници (narodnosti, veroispovesti, zanimanja, eparhije) сеју се
data-driven из fixtures фајлова: CSV за просте листе, JSONL за структуиране
редове (eparhije). Slava има засебну логику (покретни празници из
slave.jsonl) па се и даље покреће као unos_slava.

registar је у TENANT_APPS па lookup подаци живе у шеми закупца — --tenant
је обавезан.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from registar.mock.tenant_ctx import with_tenant
from registar.models import Eparhija, Narodnost, Veroispovest, Zanimanje

FIXTURES = settings.BASE_DIR / "fixtures"


@dataclass(frozen=True)
class Sifarnik:
    model: type
    fajl: str
    kljucevi: tuple[str, ...]
    dopunska: tuple[str, ...] = ()


SIFARNICI = [
    Sifarnik(Narodnost, "narodnosti.csv", ("naziv",)),
    Sifarnik(Veroispovest, "veroispovesti.csv", ("naziv",)),
    Sifarnik(Zanimanje, "zanimanja.csv", ("sifra", "naziv")),
    Sifarnik(Eparhija, "eparhije.jsonl", ("naziv",), ("nivo", "sediste")),
]


class Command(BaseCommand):
    help = "Сеје референтне (lookup) табеле у задат tenant."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Schema name тенанта.")

    def handle(self, *args, **opts):
        with with_tenant(opts["tenant"]) as tenant:
            for sifarnik in SIFARNICI:
                novih = self._zasej(sifarnik)
                self.stdout.write(
                    self.style.MIGRATE_HEADING(
                        f"  → {sifarnik.model.__name__}: {novih} нових"
                    )
                )
            self.stdout.write(self.style.MIGRATE_HEADING("  → Slava"))
            call_command("unos_slava")
            self.stdout.write(
                self.style.SUCCESS(f"Lookup табеле напуњене у {tenant.schema_name!r}.")
            )

    def _zasej(self, sifarnik: Sifarnik) -> int:
        novih = 0
        for podaci in self._redovi(sifarnik):
            kljuc = {k: podaci[k] for k in sifarnik.kljucevi}
            dopunska = {k: podaci[k] for k in sifarnik.dopunska}
            _, kreiran = sifarnik.model.objects.get_or_create(
                **kljuc, defaults=dopunska
            )
            novih += kreiran
        return novih

    def _redovi(self, sifarnik: Sifarnik):
        polja = sifarnik.kljucevi + sifarnik.dopunska
        with open(FIXTURES / sifarnik.fajl, encoding="utf-8") as fajl:
            if sifarnik.fajl.endswith(".jsonl"):
                for linija in fajl:
                    linija = linija.strip()
                    if linija:
                        yield json.loads(linija)
            else:
                for red in csv.reader(fajl, delimiter=";"):
                    vrednosti = [c.strip() for c in red]
                    if len(vrednosti) < len(polja) or not any(vrednosti):
                        continue
                    yield dict(zip(polja, vrednosti))
