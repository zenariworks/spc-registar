import random

from django.core.management.base import BaseCommand
from registar.models import Opstina

opstine = [
    "Општина 1",
    "Општина 2",
    "Општина 3",
    "Општина 4",
    "Општина 5",
    # ...
]


def unesi_opstinu(naziv: str | Opstina | None) -> tuple[Opstina, bool]:
    if isinstance(naziv, Opstina):
        return naziv, False
    naziv = naziv if naziv else random.choice(opstine)
    opstina, uneto = Opstina.objects.get_or_create(naziv=naziv)
    return opstina, uneto


class Command(BaseCommand):
    help = "Унос општина и повезивање са државама"

    def handle(self, *args, **kwargs):
        for naziv in opstine:
            opstina, uneto = unesi_opstinu(naziv)
            if uneto:
                info = f"Додата општина `{opstina}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Општина `{opstina}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
