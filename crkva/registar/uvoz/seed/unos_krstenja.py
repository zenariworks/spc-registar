"""Сеје крштења: постојеће особе као дете, родитељи, кум и свештеник (mock извор).

Сви случајни избори иду кроз модул `random`, па `--seed N` даје исте податке;
редослед позива `random` је део понашања и не сме да се мења. Избор деце
(`order_by("?")`) ради база и `--seed` га не покрива.
"""

from __future__ import annotations

import random as random_module
from datetime import timedelta
from typing import NamedTuple

from django.core.management.base import BaseCommand, CommandError
from registar.mock import constraints
from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Krstenje, Osoba, Svestenik

GODINE_PUNOLETSTVA = 18
"""Особа је одрасла (може бити родитељ или кум) од ових година."""

GODINE_DETETA = 5
"""Крштава се дете млађе од овога."""


class Ucesnici(NamedTuple):
    """Одрасли и свештеници из којих се бирају улоге уз дете."""

    muskarci: list[Osoba]
    zene: list[Osoba]
    svestenici: list[Svestenik]


class Uloge(NamedTuple):
    """Особе изабране за једно крштење."""

    otac: Osoba
    majka: Osoba
    kum: Osoba
    svestenik: Svestenik | None


def _pre_godina(godine: int):
    """Данашњи датум пре `godine` година."""
    return g.TODAY.replace(year=g.TODAY.year - godine)


def ucitaj(count: int) -> tuple[list[Osoba], Ucesnici]:
    """Деца (највише `count`, насумично) и одрасли оба пола са свештеницима.

    Без деце или без одраслих оба пола диже CommandError.
    """
    punoletni = _pre_godina(GODINE_PUNOLETSTVA)
    deca = list(
        Osoba.objects.filter(datum_rodjenja__gt=_pre_godina(GODINE_DETETA)).order_by(
            "?"
        )[:count]
    )
    ucesnici = Ucesnici(
        muskarci=list(Osoba.objects.filter(pol="М", datum_rodjenja__lte=punoletni)),
        zene=list(Osoba.objects.filter(pol="Ж", datum_rodjenja__lte=punoletni)),
        svestenici=list(Svestenik.objects.all()),
    )
    if not deca:
        raise CommandError(
            "Нема деце (Osoba млађи од 5) — повећај --count за unos_parohijana."
        )
    if not ucesnici.muskarci or not ucesnici.zene:
        raise CommandError("Нема довољно одраслих оба пола за родитеље.")
    return deca, ucesnici


def izaberi_uloge(ucesnici: Ucesnici) -> Uloge:
    """Отац, мајка, кум (било ког пола) и свештеник ако их има, тим редом."""
    return Uloge(
        otac=random_module.choice(ucesnici.muskarci),
        majka=random_module.choice(ucesnici.zene),
        kum=random_module.choice(ucesnici.muskarci + ucesnici.zene),
        svestenik=(
            random_module.choice(ucesnici.svestenici) if ucesnici.svestenici else None
        ),
    )


def proveri(dete: Osoba, datum, uloge: Uloge) -> None:
    """Правила крштења: датум после рођења, полови родитеља, без самопозивања."""
    constraints.assert_krstenje(
        dete.datum_rodjenja,
        datum,
        otac_gender=uloge.otac.pol,
        majka_gender=uloge.majka.pol,
    )
    constraints.assert_no_self_reference(
        dete.uid, [uloge.otac.uid, uloge.majka.uid, uloge.kum.uid], "дете"
    )


def podaci_krstenja(redni: int, dete: Osoba, datum, uloge: Uloge) -> dict:
    """Поља крштења; `redni` почиње од 0, по 50 уписа на страни.

    Место регистрације, па број дана до регистрације (1–7) се бирају тим
    редом.
    """
    return {
        "godina_registracije": datum.year,
        "redni_broj": redni + 1,
        "knjiga": 1,
        "strana": (redni // 50) + 1,
        "broj": redni + 1,
        "datum": datum,
        "dete": dete,
        "otac": uloge.otac,
        "majka": uloge.majka,
        "kum": uloge.kum,
        "svestenik": uloge.svestenik,
        "zivorodjeno": True,
        "po_redu": 1,
        "vanbracno": False,
        "blizanac": False,
        "telesna_mana": False,
        "mesto_registracije": g.rand_place(),
        "datum_registracije": datum + timedelta(days=random_module.randint(1, 7)),
    }


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
                self._obrisi_sve()
            deca, ucesnici = ucitaj(opts["count"])
            created = self._sej(deca, ucesnici)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Креирано {created} крштења у {tenant.schema_name!r}."
                )
            )

    def _obrisi_sve(self) -> None:
        """Брише сва крштења у тенанту (--reset)."""
        n = Krstenje.objects.count()
        Krstenje.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Обрисано {n} крштења."))

    @staticmethod
    def _sej(deca: list[Osoba], ucesnici: Ucesnici) -> int:
        """Једно крштење по детету; датум крштења је између рођења и данас."""
        for redni, dete in enumerate(deca):
            uloge = izaberi_uloge(ucesnici)
            datum = g.rand_date_between(dete.datum_rodjenja, g.TODAY)
            proveri(dete, datum, uloge)
            Krstenje.objects.create(**podaci_krstenja(redni, dete, datum, uloge))
        return len(deca)
