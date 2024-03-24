import random

from django.core.management.base import BaseCommand
from registar.models import Svestenik, Ulica
from registar.models.drzava import Drzava
from registar.models.mesto import Mesto
from registar.models.opstina import Opstina

from .unos_drzava import unesi_drzavu
from .unos_mesta import unesi_mesto
from .unos_opstina import unesi_opstinu

ulice = [
    "Улица 1",
    "Улица 2",
    "Улица 3",
    "Улица 4",
    "Улица 5",
    # ...
]


def unesi_ulicu(
    naziv: str | None = None,
    mesto_naziv: str | Mesto | None = None,
    opstina_naziv: str | Opstina | None = None,
    drzava_naziv: str | Drzava | None = None,
    svestenik: Svestenik | None = None,
) -> tuple[Ulica, bool]:
    naziv = naziv or random.choice(ulice)
    svestenik = svestenik or Svestenik.objects.order_by("?").first()
    ulica, uneto = Ulica.objects.get_or_create(
        naziv=naziv,
        defaults={
            "drzava": unesi_drzavu(drzava_naziv)[0],
            "opstina": unesi_opstinu(opstina_naziv)[0],
            "mesto": unesi_mesto(mesto_naziv)[0],
            "svestenik": svestenik,
        },
    )
    return ulica, uneto


class Command(BaseCommand):
    help = "Унос улица и повезивање са местом"

    def handle(self, *args, **kwargs):
        for naziv in ulice:
            ulica, uneto = unesi_ulicu(naziv)
            if uneto:
                info = f"Додата улица `{ulica}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Улица `{ulica}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
