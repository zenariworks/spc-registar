"""Сеје венчања тако што одрасле парохијане упарује као женика и невесту."""

from __future__ import annotations

import random as random_module
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from registar.mock import constraints
from registar.mock import generators as g
from registar.mock.tenant_ctx import with_tenant
from registar.models import Osoba, Svestenik, Vencanje

PUNOLETSTVO = 18
"""Године од којих се особа сматра одраслом."""

NAJVECA_RAZLIKA_GODINA = 25
"""Највећа дозвољена разлика у годинама између супружника."""

VENCANJA_PO_STRANI = 50
"""Колико венчања стаје на једну страну матичне књиге."""


def _odrasli(pol: str) -> list[Osoba]:
    """Одрасле особе датог пола, насумичним редом."""
    granica = g.TODAY.replace(year=g.TODAY.year - PUNOLETSTVO)
    return list(
        Osoba.objects.filter(pol=pol, datum_rodjenja__lte=granica).order_by("?")
    )


def _parovi(muskarci: list[Osoba], zene: list[Osoba]) -> list[tuple[Osoba, Osoba]]:
    """Сви парови мушкарац–жена чија разлика у годинама није превелика."""
    return [
        (m, f)
        for m in muskarci
        for f in zene
        if abs(g.age(m.datum_rodjenja) - g.age(f.datum_rodjenja))
        <= NAJVECA_RAZLIKA_GODINA
    ]


def _datum_vencanja(m: Osoba, f: Osoba) -> date | None:
    """Насумичан датум од пунолетства млађег супружника до данас.

    None кад млађи супружник још није пунолетан, па пар не може бити венчан.
    """
    mladji = max(m.datum_rodjenja, f.datum_rodjenja)
    punoletstvo = mladji.replace(year=mladji.year + PUNOLETSTVO)
    if punoletstvo >= g.TODAY:
        return None
    return g.rand_date_between(punoletstvo, g.TODAY)


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
            raise CommandError("unos_vencanja подржава само --from mock.")

        with with_tenant(opts["tenant"]) as tenant:
            if opts["reset"]:
                self._obrisi_sve()

            muskarci = _odrasli("М")
            zene = _odrasli("Ж")
            svestenici = list(Svestenik.objects.all())
            if not muskarci or not zene:
                raise CommandError("Нема довољно одраслих оба пола.")

            parovi = _parovi(muskarci, zene)
            if not parovi:
                raise CommandError(
                    "Нема компатибилних парова (разлика година > 25 за све)."
                )
            random_module.shuffle(parovi)

            created = self._vencaj(parovi, muskarci, svestenici, opts["count"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Креирано {created} венчања у {tenant.schema_name!r}."
                )
            )

    def _obrisi_sve(self) -> None:
        """Брише сва постојећа венчања (--reset)."""
        n = Vencanje.objects.count()
        Vencanje.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Обрисано {n} венчања."))

    def _vencaj(
        self,
        parovi: list[tuple[Osoba, Osoba]],
        muskarci: list[Osoba],
        svestenici: list[Svestenik],
        count: int,
    ) -> int:
        """Венчава парове редом док не направи `count` венчања.

        Свака особа може бити у највише једном пару, па се пар са већ
        искоришћеном особом прескаче. И пар који не може да се венча
        (`_upisi_vencanje` враћа False) троши своје особе.
        """
        iskorisceni: set = set()
        created = 0
        for m, f in parovi:
            if created >= count:
                break
            if m.uid in iskorisceni or f.uid in iskorisceni:
                continue
            iskorisceni.add(m.uid)
            iskorisceni.add(f.uid)
            if self._upisi_vencanje(m, f, muskarci, svestenici, created):
                created += 1
        return created

    @staticmethod
    def _upisi_vencanje(
        m: Osoba,
        f: Osoba,
        muskarci: list[Osoba],
        svestenici: list[Svestenik],
        redni: int,
    ) -> bool:
        """Уписује једно венчање; False ако пар не може да се венча.

        Кум је одрасли мушкарац који није један од супружника. Насумични
        избори (датум, кум, свештеник) иду истим редом као раније, па исти
        `--seed` даје исте податке.
        """
        datum = _datum_vencanja(m, f)
        if datum is None:
            return False
        kumovi = [p for p in muskarci if p.uid not in (m.uid, f.uid)]
        if not kumovi:
            return False
        kum = random_module.choice(kumovi)
        svestenik = random_module.choice(svestenici) if svestenici else None

        constraints.assert_spouse_pair(
            "М", m.datum_rodjenja, "Ж", f.datum_rodjenja, datum
        )
        constraints.assert_no_self_reference(m.uid, [f.uid, kum.uid], "женик")

        Vencanje.objects.create(
            godina_registracije=datum.year,
            redni_broj=redni + 1,
            knjiga=1,
            strana=(redni // VENCANJA_PO_STRANI) + 1,
            broj=redni + 1,
            datum=datum,
            zenik=m,
            zenik_rb_brak=1,
            nevesta=f,
            nevesta_rb_brak=1,
            kum=kum,
            svestenik=svestenik,
        )
        return True
