from django.core.management.base import BaseCommand
from registar.models import Opstina

from .unos_drzava import unesi_drzavu


class Command(BaseCommand):
    help = "Унос општина и повезивање са државама"

    opstine_i_drzave = [
        ("Општина 1", "Србија"),
        ("Општина 2", "Босна и Херцеговина"),
        # ...
    ]

    def handle(self, *args, **kwargs):
        for naziv, drzava_naziv in self.opstine_i_drzave:
            drzava, _ = unesi_drzavu(drzava_naziv)
            _, created = Opstina.objects.get_or_create(naziv=naziv, drzava=drzava)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Додата општина: `{naziv}, {drzava_naziv}`")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Општина `{naziv}, {drzava_naziv}` већ постоји."
                    )
                )
