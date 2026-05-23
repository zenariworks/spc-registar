"""Seed Vencanje rows by pairing existing adult Parohijani as zenik+nevesta."""

from __future__ import annotations

import random as random_module

from django.core.management.base import BaseCommand, CommandError
from registar.mock import constraints
from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Osoba, Svestenik, Vencanje


class Command(BaseCommand):
    help = "Сеје венчања (мушкарац+жена одрасли, разлика година ≤ 25)."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", default="mock")
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--count", type=int, default=10)
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])
        if opts["source"] != "mock":
            raise CommandError("seed_vencanja подржава само --from mock.")

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                n = Vencanje.objects.count()
                Vencanje.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"Обрисано {n} венчања."))

            adult_cutoff = g.TODAY.replace(year=g.TODAY.year - 18)
            males = list(
                Osoba.objects.filter(
                    pol="М", datum_rodjenja__lte=adult_cutoff
                ).order_by("?")
            )
            females = list(
                Osoba.objects.filter(
                    pol="Ж", datum_rodjenja__lte=adult_cutoff
                ).order_by("?")
            )
            svestenici = list(Svestenik.objects.all())

            if not males or not females:
                raise CommandError("Нема довољно одраслих оба пола.")

            # Build candidate pairs respecting age gap ≤ 25
            pairs = []
            for m in males:
                for f in females:
                    diff = abs(g.age(m.datum_rodjenja) - g.age(f.datum_rodjenja))
                    if diff <= 25:
                        pairs.append((m, f))
            if not pairs:
                raise CommandError(
                    "Нема компатибилних парова (разлика година > 25 за све)."
                )
            random_module.shuffle(pairs)

            used: set = set()
            created = 0
            for m, f in pairs:
                if created >= opts["count"]:
                    break
                if m.uid in used or f.uid in used:
                    continue
                used.add(m.uid)
                used.add(f.uid)

                # datum: 1-30 years ago
                latest_birth = max(m.datum_rodjenja, f.datum_rodjenja)
                adult_date = latest_birth.replace(year=latest_birth.year + 18)
                if adult_date >= g.TODAY:
                    continue  # cannot be married yet
                datum = g.rand_date_between(adult_date, g.TODAY)

                # kum = male adult, NOT one of the spouses
                kum_pool = [p for p in males if p.uid not in (m.uid, f.uid)]
                if not kum_pool:
                    continue
                kum = random_module.choice(kum_pool)
                svestenik = random_module.choice(svestenici) if svestenici else None

                # Enforce
                constraints.assert_spouse_pair(
                    "М", m.datum_rodjenja, "Ж", f.datum_rodjenja, datum
                )
                constraints.assert_no_self_reference(m.uid, [f.uid, kum.uid], "женик")

                Vencanje.objects.create(
                    godina_registracije=datum.year,
                    redni_broj=created + 1,
                    knjiga=1,
                    strana=(created // 50) + 1,
                    broj=created + 1,
                    datum=datum,
                    zenik=m,
                    zenik_rb_brak=1,
                    nevesta=f,
                    nevesta_rb_brak=1,
                    kum=kum,
                    svestenik=svestenik,
                )
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Креирано {created} венчања у {tenant.schema_name!r}."
                )
            )
