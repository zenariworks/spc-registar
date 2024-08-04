"""
Модул за унос свећеника у базу података.
"""

import random
from datetime import date

from django.core.management.base import BaseCommand
from registar.models import Parohija, Svestenik
from registar.models.svestenik import zvanja


def unesi_svestenika(
    ime: str | None = None,
    prezime: str | None = None,
    mesto_rodjenja: str | None = None,
    datum_rodjenja: str | None = None,
    zvanje: str | None = None,
    parohija: str | None = None,
) -> Svestenik:
    """
    Уноси новог свештеника у базу података.

    :param ime: Име свештеника
    :param prezime: Презиме свештеника
    :param mesto_rodjenja: Место рођења свештеника
    :param datum_rodjenja: Датум рођења свештеника
    :param zvanje: Звање свештеника
    :param parohija: Парохија свештеника
    :return: Креиран објекат свештеника
    """
    svestenik = Svestenik.objects.create(
        ime=ime,
        prezime=prezime,
        mesto_rodjenja=mesto_rodjenja,
        datum_rodjenja=datum_rodjenja,
        zvanje=zvanje,
        parohija=parohija or Parohija.objects.order_by("?").first(),
    )
    return svestenik


class Command(BaseCommand):
    """
    Класа Ђанго команде за унос свећеника у базу података.
    """

    help = "Унос свештеника у базу података."

    def add_arguments(self, parser):
        parser.add_argument(
            "broj", type=int, help="Број свештеника који ће бити додати."
        )

    def handle(self, *args, **options):
        број = options["broj"]
        for _ in range(број):
            име = f"Ime{_}"
            презиме = f"Prezime{_}"
            место_родјења = f"Mesto{_}"
            датум_родјења = date(1970 + _ % 50, (_ % 12) + 1, (_ % 28) + 1)
            звање = random.choice(zvanja)[0]
            свештеник = unesi_svestenika(
                име, презиме, место_родјења, датум_родјења, звање
            )

            self.stdout.write(self.style.SUCCESS(f"Додат свештеник: {свештеник}"))
