from django.core.management.base import BaseCommand
from registar.models import Mesto

from .unos_opstina import unesi_opstinu

mesta_opstine_drzave = [
    ("Место 1", "Општина 1", "Србија"),
    ("Место 2", "Општина 2", "Босна и Херцеговина"),
    ("Место 3", "Општина 1", "Србија"),
    # ...
]


def unesi_mesto(naziv, naziv_opstine, naziv_drzave) -> tuple[Mesto, bool]:
    opstina, _ = unesi_opstinu(naziv_opstine, naziv_drzave)
    return Mesto.objects.get_or_create(naziv=naziv, defaults={"opstina": opstina})


class Command(BaseCommand):
    help = "Унос места и повезивање са општинама"

    def handle(self, *args, **kwargs):
        for naziv, opstina_naziv, drzava_naziv in mesta_opstine_drzave:
            mesto, uneta = unesi_mesto(naziv, opstina_naziv, drzava_naziv)
            if uneta:
                info = f"Додато место `{mesto}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Место `{mesto}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
