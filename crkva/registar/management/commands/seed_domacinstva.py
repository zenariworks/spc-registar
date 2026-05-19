"""Wire existing Parohijani into Domacinstva with Ukucani roles.

Picks adult parohijani as domacin (head), optionally adds same-tenant
opposite-gender adult as spouse + 0-3 children as members. Each
household gets a random Adresa + Slava (if present in the tenant).

Constraints enforced (mock.constraints):
- domacin must be adult
- spouse opposite gender + adult
- no self-reference
"""
from __future__ import annotations

import random as random_module

from django.core.management.base import BaseCommand, CommandError

from registar.mock import constraints, generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Adresa, Domacinstvo, Parohijan, Ukucanin
from kalendar.models import Slava


class Command(BaseCommand):
    help = "Сеје домаћинства повезивањем постојећих парохијана."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", default="mock")
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--count", type=int, default=33,
                            help="Колико домаћинстава креирати (default 33).")
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument("--reset", action="store_true",
                            help="ОПАСНО: брише сва домаћинства + укућане у тенанту.")

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])
        if opts["source"] != "mock":
            raise CommandError("seed_domacinstva подржава само --from mock.")

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                u_count = Ukucanin.objects.count()
                d_count = Domacinstvo.objects.count()
                Ukucanin.objects.all().delete()
                Domacinstvo.objects.all().delete()
                self.stdout.write(self.style.WARNING(
                    f"Обрисано {d_count} домаћинстава + {u_count} укућана."
                ))

            # Pre-fetch pools
            adults_male = list(Parohijan.objects.filter(
                pol="М", datum_rodjenja__lte=g.TODAY.replace(year=g.TODAY.year - 18)
            ).order_by("?")[: opts["count"] * 2])
            adults_female = list(Parohijan.objects.filter(
                pol="Ж", datum_rodjenja__lte=g.TODAY.replace(year=g.TODAY.year - 18)
            ).order_by("?")[: opts["count"] * 2])
            children = list(Parohijan.objects.filter(
                datum_rodjenja__gt=g.TODAY.replace(year=g.TODAY.year - 18)
            ).order_by("?"))
            addresses = list(Adresa.objects.all())
            slavas = list(Slava.objects.all()[:30])

            if not adults_male and not adults_female:
                raise CommandError(
                    "Нема одраслих парохијана у тенанту — прво "
                    "`seed_parohijani` са довољно записа."
                )

            used_parohijani: set = set()
            created = 0

            for _ in range(opts["count"]):
                # Pick domacin — prefer male
                pool = adults_male or adults_female
                candidates = [p for p in pool if p.uid not in used_parohijani]
                if not candidates:
                    self.stdout.write(self.style.WARNING(
                        "Исцрпљени одрасли — стајем рано."
                    ))
                    break
                domacin = random_module.choice(candidates)
                used_parohijani.add(domacin.uid)
                constraints.assert_adult(domacin.datum_rodjenja, role="домаћин")

                dom = Domacinstvo.objects.create(
                    domacin=domacin,
                    adresa=random_module.choice(addresses) if addresses else None,
                    slava=random_module.choice(slavas) if slavas else None,
                    slavska_vodica=random_module.random() < 0.7,
                    vaskrsnja_vodica=random_module.random() < 0.6,
                )

                # 70% chance to add a spouse of opposite gender
                if random_module.random() < 0.7:
                    spouse_pool = adults_female if domacin.pol == "М" else adults_male
                    spouse_candidates = [
                        p for p in spouse_pool if p.uid not in used_parohijani
                    ]
                    if spouse_candidates:
                        spouse = random_module.choice(spouse_candidates)
                        used_parohijani.add(spouse.uid)
                        # Assert opposite gender + adult
                        assert spouse.pol != domacin.pol, "spouse same gender"
                        constraints.assert_adult(spouse.datum_rodjenja, role="супружник")
                        constraints.assert_no_self_reference(
                            domacin.uid, [spouse.uid], "супружник"
                        )
                        Ukucanin.objects.create(
                            domacinstvo=dom,
                            osoba=spouse,
                            uloga="супружник",
                        )

                # 0-3 children
                n_kids = random_module.choices([0, 1, 2, 3], weights=[20, 35, 30, 15])[0]
                kid_candidates = [c for c in children if c.uid not in used_parohijani]
                for kid in random_module.sample(
                    kid_candidates, min(n_kids, len(kid_candidates))
                ):
                    used_parohijani.add(kid.uid)
                    Ukucanin.objects.create(
                        domacinstvo=dom,
                        osoba=kid,
                        uloga="дете",
                    )

                created += 1

            self.stdout.write(self.style.SUCCESS(
                f"Креирано {created} домаћинстава у {tenant.schema_name!r}."
            ))
