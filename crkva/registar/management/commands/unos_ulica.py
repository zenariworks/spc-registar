import random

from django.core.management.base import BaseCommand
from registar.models import Svestenik, Ulica

from crkva.registar.models.drzava import Drzava
from crkva.registar.models.mesto import Mesto
from crkva.registar.models.opstina import Opstina

from .unos_drzava import unesi_drzavu
from .unos_mesta import unesi_mesto
from .unos_opstina import unesi_opstinu

ulice = [
    ("Улица 1", "Место 1", "Општина 1", "Србија"),
    ("Улица 2", "Место 2", "Општина 2", "Босна и Херцеговина"),
    # ...
]


def unesi_ulicu(
    naziv: str | None,
    mesto_naziv: str | Mesto | None,
    opstina_naziv: str | Opstina | None,
    drzava_naziv: str | Drzava | None,
    svestenik: Svestenik | None,
) -> tuple[Ulica, bool]:
    naziv = naziv or random.choice([ulica[0] for ulica in ulice])

    drzava = unesi_drzavu(drzava_naziv)
    opstina = unesi_opstinu(opstina_naziv)
    mesto = unesi_mesto(mesto_naziv)

    # Odredi svestenika: koristi prosleđenog svestenika ili izaberi nasumično ako nije dat.
    svestenik = svestenik or Svestenik.objects.order_by("?").first()

    ulica, uneto = Ulica.objects.get_or_create(
        naziv=naziv,
        defaults={
            "drzava": drzava,
            "mesto": mesto,
            "opstina": opstina,
            "svestenik": svestenik,
        },
    )

    return ulica, uneto


class Command(BaseCommand):
    help = "Унос улица и повезивање са местом"

    def handle(self, *args, **kwargs):
        for naziv, mestо, opstinа, drzavа in ulice:
            ulica, uneto = unesi_ulicu(naziv, mestо, opstinа, drzavа)
            if uneto:
                info = f"Додата улица `{ulica}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Улица `{ulica}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
