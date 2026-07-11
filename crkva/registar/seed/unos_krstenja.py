"""Seed Krstenje rows by wiring existing Parohijani as dete + parents + kum."""

from __future__ import annotations

import random as random_module
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from registar.mock import constraints
from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Krstenje, Osoba, Svestenik


class Command(BaseCommand):
    help = "Сеје крштења (бира децу + родитеље + кумове + свештеника из постојећих)."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="source", default="mock")
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--count", type=int, default=25)
        parser.add_argument("--seed", type=int, default=None)
        parser.add_argument(
            "--reset", action="store_true", help="ОПАСНО: брише сва крштења у тенанту."
        )

    def handle(self, *args, **opts):
        if opts["seed"] is not None:
            random_module.seed(opts["seed"])
        if opts["source"] != "mock":
            raise CommandError("unos_krstenja подржава само --from mock.")

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                n = Krstenje.objects.count()
                Krstenje.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"Обрисано {n} крштења."))

            adult_cutoff = g.TODAY.replace(year=g.TODAY.year - 18)
            kids = list(
                Osoba.objects.filter(
                    datum_rodjenja__gt=g.TODAY.replace(year=g.TODAY.year - 5)
                ).order_by("?")[: opts["count"]]
            )
            adult_males = list(
                Osoba.objects.filter(pol="М", datum_rodjenja__lte=adult_cutoff)
            )
            adult_females = list(
                Osoba.objects.filter(pol="Ж", datum_rodjenja__lte=adult_cutoff)
            )
            svestenici = list(Svestenik.objects.all())

            if not kids:
                raise CommandError(
                    "Нема деце (Osoba млађи од 5) — повећај --count за "
                    "unos_parohijana."
                )
            if not adult_males or not adult_females:
                raise CommandError("Нема довољно одраслих оба пола за родитеље.")

            created = 0
            for i, dete in enumerate(kids[: opts["count"]]):
                otac = random_module.choice(adult_males)
                majka = random_module.choice(adult_females)
                kum = random_module.choice(adult_males + adult_females)
                svestenik = random_module.choice(svestenici) if svestenici else None

                # datum_krstenja between birth and today
                datum = g.rand_date_between(dete.datum_rodjenja, g.TODAY)

                # Enforce constraints
                constraints.assert_krstenje(
                    dete.datum_rodjenja,
                    datum,
                    otac_gender=otac.pol,
                    majka_gender=majka.pol,
                )
                constraints.assert_no_self_reference(
                    dete.uid, [otac.uid, majka.uid, kum.uid], "дете"
                )

                Krstenje.objects.create(
                    godina_registracije=datum.year,
                    redni_broj=i + 1,
                    knjiga=1,
                    strana=(i // 50) + 1,
                    broj=i + 1,
                    datum=datum,
                    dete=dete,
                    otac=otac,
                    majka=majka,
                    kum=kum,
                    svestenik=svestenik,
                    zivorodjeno=True,
                    po_redu=1,
                    vanbracno=False,
                    blizanac=False,
                    telesna_mana=False,
                    mesto_registracije=g.rand_place(),
                    datum_registracije=datum
                    + timedelta(days=random_module.randint(1, 7)),
                )
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Креирано {created} крштења у {tenant.schema_name!r}."
                )
            )
