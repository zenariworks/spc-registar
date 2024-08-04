"""
Модул команде за унос адреса и повезивање са улицама.
"""

from django.core.management.base import BaseCommand
from registar.models import Adresa, Svestenik

from .unos_ulica import unesi_ulicu

adrese = [
    ("Улица 1", "1", "А", "11000", "Примедба 1"),
    ("Улица 2", "2", "", "71000", "Примедба 2"),
    ("Улица 3", "1", "А", "11000", "Примедба 1"),
    # ...
]


def unesi_adresu(
    naziv: str | None,
    broj: str | None,
    dodatak: str | None = None,
    postkod: str | None = None,
    primedba: str | None = None,
    mesto: str | None = None,
    opstina: str | None = None,
    drzava: str | None = None,
    svestenik: Svestenik | None = None,
) -> tuple[Adresa, bool]:
    """
    Уноси нову адресу у базу података или враћа постојећу.

    :param naziv: Назив улице
    :param broj: Број куће или зграде
    :param dodatak: Додатак броју (нпр. 'А')
    :param postkod: Поштански код
    :param primedba: Примедба уз адресу
    :param mesto: Место у којем се улица налази
    :param opstina: Општина у којој се улица налази
    :param drzava: Држава у којој се улица налази
    :param svestenik: Свестеник повезан са адресом
    :return: Креирана или постојећа адреса и флаг да ли је креирана нова
    """
    return Adresa.objects.get_or_create(
        ulica=unesi_ulicu(naziv, mesto, opstina, drzava, svestenik)[0],
        broj=broj,
        defaults={"dodatak": dodatak, "postkod": postkod, "primedba": primedba},
    )


class Command(BaseCommand):
    """
    Класа Ђанго команде за унос адреса и повезивање са улицама.
    """

    help = "Унос адреса и повезивање са улицама"

    def handle(self, *args, **kwargs):
        for adresa in adrese:
            (
                ulica,
                broj,
                dodatak,
                postkod,
                primedba,
            ) = adresa
            adresa, kreirana = unesi_adresu(ulica, broj, dodatak, postkod, primedba)

            if kreirana:
                output = self.style.SUCCESS(f"Додата адреса: {adresa}")
            else:
                output = self.style.WARNING(f"Адреса већ постоји: {adresa}")
            self.stdout.write(output)
