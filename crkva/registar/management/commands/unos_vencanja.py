"""Модул за попуњавање базе података насумичним венчањима."""

import random
import uuid
from datetime import date

from django.core.management.base import BaseCommand
from registar.management.commands.random_utils import RandomUtils
from registar.models import Hram, Svestenik, Vencanje

from .unos_adresa import unesi_adresu


class Command(BaseCommand):
    help = "Попуњава базу података насумичним венчањима"

    def get_or_create_svestenik(self) -> Svestenik:
        """Враћа постојећег или креира насумичног свештеника."""
        svestenici = list(Svestenik.objects.all())
        if svestenici:
            return random.choice(svestenici)

        # ако нема свештеника, направи једног
        return Svestenik.objects.create(
            uid=uuid.uuid4(),
            zvanje=random.choice(RandomUtils.zvanja),
            parohija=None,
            ime=random.choice(RandomUtils.male_names),
            prezime=random.choice(RandomUtils.surnames),
            mesto_rodjenja="Насумично место",
            datum_rodjenja=RandomUtils.random_date_of_birth(30),
        )

    def get_or_create_hram(self):
        """Враћа постојећи или креира насумични храм."""
        hramovi = list(Hram.objects.all())
        if hramovi:
            return random.choice(hramovi)
        return RandomUtils.create_random_hram(unesi_adresu)

    def create_random_vencanje(self):
        """Креира једно насумично венчање."""
        today = date.today()
        svestenik = self.get_or_create_svestenik()
        hram = self.get_or_create_hram()

        vencanje = Vencanje.objects.create(
            uid=uuid.uuid4(),
            redni_broj_vencanja_tekuca_godina=random.randint(1, 100),
            vencanje_tekuca_godina=today.year,
            knjiga=random.randint(1, 10),
            strana=random.randint(1, 500),
            tekuci_broj=random.randint(1, 1000),
            datum=RandomUtils.random_datetime().date(),
            ime_zenika=random.choice(RandomUtils.male_names),
            prezime_zenika=random.choice(RandomUtils.surnames),
            zanimanje_zenika=random.choice(RandomUtils.sample_occupations_text()),
            mesto_zenika="Београд",
            veroispovest_zenika="Православна",
            narodnost_zenika="Србин",
            adresa_zenika="Насумична адреса",
            ime_neveste=random.choice(RandomUtils.female_names),
            prezime_neveste=random.choice(RandomUtils.surnames),
            zanimanje_neveste=random.choice(RandomUtils.sample_occupations_text()),
            mesto_neveste="Нови Сад",
            veroispovest_neveste="Православна",
            narodnost_neveste="Српкиња",
            adresa_neveste="Насумична адреса",
            svekar=random.choice(RandomUtils.male_names),
            svekrva=random.choice(RandomUtils.female_names),
            tast=random.choice(RandomUtils.male_names),
            tasta=random.choice(RandomUtils.female_names),
            datum_rodjenja_zenika=RandomUtils.random_date_of_birth(25),
            mesto_rodjenja_zenika="Београд",
            datum_rodjenja_neveste=RandomUtils.random_date_of_birth(23),
            mesto_rodjenja_neveste="Нови Сад",
            zenik_rb_brak="1",
            nevesta_rb_brak="1",
            datum_ispita=RandomUtils.random_datetime().date(),
            hram=hram,
            svestenik=svestenik,
            kum=random.choice(RandomUtils.male_names),
            stari_svat=random.choice(RandomUtils.male_names),
            razresenje="Да",
            razresenje_primedba="",
            primedba="Нема примедби",
        )

        return vencanje

    def handle(self, *args, **kwargs):
        for _ in range(10):
            self.create_random_vencanje()

        self.stdout.write(
            self.style.SUCCESS("Успешно попуњена база података венчањима")
        )
