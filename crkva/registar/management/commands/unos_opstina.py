from django.core.management.base import BaseCommand
from registar.models import Opstina

from .unos_drzava import unesi_drzavu

opstine_i_drzave = [
    ("Општина 1", "Србија"),
    ("Општина 2", "Босна и Херцеговина"),
    # ...
]


def unesi_opstinu(naziv, naziv_drzave) -> tuple[Opstina, bool]:
    drzava, _ = unesi_drzavu(naziv_drzave)
    return Opstina.objects.get_or_create(naziv=naziv, defaults={"drzava": drzava})


class Command(BaseCommand):
    help = "Унос општина и повезивање са државама"

    def handle(self, *args, **kwargs):
        for naziv, drzava_naziv in opstine_i_drzave:
            opstina, uneta = unesi_opstinu(naziv, drzava_naziv)
            if uneta:
                info = f"Додата општина `{opstina}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Општина `{opstina}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
