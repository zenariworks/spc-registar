"""
Модул за попуњавање базе података насумичним венчањима.
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from registar.management.commands.random_utils import RandomUtils
from registar.models import Parohija, Parohijan, Svestenik, Vencanje

from .unos_adresa import unesi_adresu


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање базе података насумичним венчањима.
    """

    help = "Попуњава базу података насумичним венчањима"

    def random_parohijan(self, gender, min_age=0):
        """Креира насумично парохијана."""
        eligible_parohijan = Parohijan.objects.filter(
            pol=gender,
            datum_rodjenja__lte=date.today() - timedelta(days=min_age * 365.25),
        )
        if eligible_parohijan.exists():
            return random.choice(eligible_parohijan)
        else:
            return RandomUtils.create_random_parohijan(unesi_adresu, gender, min_age)

    def get_or_create_parohija(self, naziv):
        """Креира насумично парохију."""
        parohija, _ = Parohija.objects.get_or_create(naziv=naziv)
        return parohija

    def create_random_svestenik(self) -> Svestenik:
        """Креира насумично свештеника."""
        parohije = [
            self.get_or_create_parohija("Парохија 1"),
            self.get_or_create_parohija("Парохија 2"),
            self.get_or_create_parohija("Парохија 3"),
            self.get_or_create_parohija("Парохија 4"),
        ]

        svestenik = Svestenik(
            zvanje=random.choice(RandomUtils.zvanja),
            parohija=random.choice(parohije),
            ime=random.choice(RandomUtils.male_names),
            prezime=random.choice(RandomUtils.surnames),
            mesto_rodjenja="Насумично место",
            datum_rodjenja=RandomUtils.random_date_of_birth(25),
        )
        svestenik.save()
        return svestenik

    def create_random_vencanje(self):
        """Креира насумично венчање."""
        vencanje = Vencanje(
            knjiga=random.randint(1, 100),
            strana=random.randint(1, 500),
            tekuci_broj=random.randint(1, 1000),
            datum=RandomUtils.random_datetime().date(),
            zenik=self.random_parohijan("М", 18),
            zenik_rb_brak=random.randint(1, 3),
            nevesta=self.random_parohijan("Ж", 18),
            nevesta_rb_brak=random.randint(1, 3),
            hram=RandomUtils.create_random_hram(unesi_adresu),
            svestenik=self.create_random_svestenik(),
            datum_ispita=RandomUtils.random_datetime().date(),
            primedba="Насумична примедба...",
        )
        vencanje.save()

    def handle(self, *args, **kwargs):
        for _ in range(10):
            self.create_random_vencanje()

        self.stdout.write(
            self.style.SUCCESS("Успешно попуњена база података са насумичним подацима")
        )
