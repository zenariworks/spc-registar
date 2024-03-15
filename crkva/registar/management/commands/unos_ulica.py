from django.core.management.base import BaseCommand
from registar.models import Ulica

from .unos_mesta import unesi_mesto

ulice_i_mesta = [
    ("Улица 1", "Место 1", "Општина 1", "Србија"),
    ("Улица 2", "Место 2", "Општина 2", "Босна и Херцеговина"),
    # Dodajte ostale ulice i odgovarajuće mesta, opštine i države po potrebi
]


def unesi_ulicu(
    naziv, naziv_mesta, naziv_opstine, naziv_drzave, svestenik_id
) -> tuple[Ulica, bool]:
    mesto, _ = unesi_mesto(naziv_mesta, naziv_opstine, naziv_drzave)
    return Ulica.objects.get_or_create(
        naziv=naziv, defaults={"mesto": mesto, "svestenik": svestenik_id}
    )


class Command(BaseCommand):
    help = "Унос улица и повезивање са местом"

    def handle(self, *args, **kwargs):
        for naziv_ulice, naziv_mesta, naziv_opstine, naziv_drzave in ulice_i_mesta:
            svestenik_id = 1
            ulica, uneta = unesi_ulicu(
                naziv_ulice, naziv_mesta, naziv_opstine, naziv_drzave, svestenik_id
            )
            if uneta:
                info = f"Додата улица `{ulica}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Улица `{ulica}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
