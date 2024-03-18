# unos_adresa.py
from django.core.management.base import BaseCommand
from registar.models import Adresa

from .unos_ulica import unesi_ulicu

adrese_i_ulice = [
    ("Улица 1", "1", "А", "11000", "Напомена 1", "Место 1", "Општина 1", "Србија"),
    (
        "Улица 2",
        "2",
        "",
        "71000",
        "Напомена 2",
        "Место 2",
        "Општина 2",
        "Босна и Херцеговина",
    ),
    ("Улица 3", "1", "А", "11000", "Напомена 1", "Место 1", "Општина 1", "Холандија"),
    # ...
]


def unesi_adresu(
    naziv,
    broj,
    dodatak,
    postkod,
    napomena,
    mesto,
    opstina,
    drzava,
    svestenik_id,
) -> tuple[Adresa, bool]:
    ulica, _ = unesi_ulicu(naziv, mesto, opstina, drzava, svestenik_id)
    return Adresa.objects.get_or_create(
        ulica=ulica,
        broj=broj,
        defaults={"dodatak": dodatak, "postkod": postkod, "napomena": napomena},
    )


class Command(BaseCommand):
    help = "Унос адреса и повезивање са улицама"

    def handle(self, *args, **kwargs):
        for adresa in adrese_i_ulice:
            (
                ulica,
                broj,
                dodatak,
                postkod,
                napomena,
                mesto,
                opstina,
                drzava,
            ) = adresa
            svestenik_id = 1
            adresa, kreirana = unesi_adresu(
                ulica,
                broj,
                dodatak,
                postkod,
                napomena,
                mesto,
                opstina,
                drzava,
                svestenik_id,
            )

            if kreirana:
                self.stdout.write(self.style.SUCCESS(f"Додата адреса: {adresa}"))
            else:
                self.stdout.write(self.style.WARNING(f"Адреса већ постоји: {adresa}"))
