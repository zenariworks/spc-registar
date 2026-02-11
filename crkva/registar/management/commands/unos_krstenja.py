"""
Модул за попуњавање базе података насумичним парохијанима.
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from registar.management.commands.random_utils import RandomUtils
from registar.models import Hram, Krstenje, Parohija, Parohijan, Svestenik

from .unos_adresa import unesi_adresu


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање базе података насумичним парохијанима.
    """

    help = "Попуњава базу података насумичним парохијанима"

    def random_parohijan(self, gender, min_age=0):
        """Креира насумично парохијана."""
        eligible_parohijan = Parohijan.objects.filter(
            pol=gender,
            datum_rodjenja__lte=date.today() - timedelta(days=min_age * 365.25),
        )
        if eligible_parohijan.exists():
            return random.choice(eligible_parohijan)
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

    def create_random_krstenje(self, _parohijan):
        """Креира насумично крштење."""
        dete_pol = "М" if random.choice([True, False]) else "Ж"
        dete_ime = random.choice(
            RandomUtils.male_names if dete_pol == "М" else RandomUtils.female_names
        )
        otac = self.random_parohijan("М", min_age=20)
        majka = self.random_parohijan("Ж", min_age=20)
        kum = self.random_parohijan(
            "М" if random.choice([True, False]) else "Ж", min_age=20
        )
        svestenik = self.create_random_svestenik()
        hram = Hram.objects.order_by("?").first()

        today = date.today()
        datum_rodjenja = RandomUtils.random_date_of_birth(0, 1)

        krstenje = Krstenje(
            redni_broj=random.randint(1, 1000),
            godina_registracije=today.year,
            knjiga=random.randint(1, 100),
            broj=random.randint(1, 1000),
            strana=random.randint(1, 500),
            datum=RandomUtils.random_datetime().date(),
            vreme=RandomUtils.random_datetime().time(),
            hram=hram,
            adresa_deteta_grad="Београд",
            adresa_deteta_ulica="Улица " + str(random.randint(1, 100)),
            adresa_deteta_broj=str(random.randint(1, 100)),
            datum_rodjenja=datum_rodjenja,
            vreme_rodjenja=RandomUtils.random_datetime().time(),
            mesto_rodjenja="Београд",
            ime_deteta=dete_ime,
            pol_deteta=dete_pol,
            ime_oca=otac.ime,
            prezime_oca=otac.prezime,
            zanimanje_oca=otac.zanimanje,
            veroispovest_oca=otac.veroispovest,
            narodnost_oca=otac.narodnost,
            ime_majke=majka.ime,
            prezime_majke=majka.prezime,
            zanimanje_majke=majka.zanimanje,
            veroispovest_majke=majka.veroispovest,
            dete_rodjeno_zivo=True,
            dete_po_redu_po_majci=str(random.randint(1, 10)),
            dete_vanbracno=random.choice([True, False]),
            dete_blizanac=random.choice([True, False]),
            dete_sa_telesnom_manom=random.choice([True, False]),
            svestenik=svestenik,
            ime_kuma=kum.ime,
            prezime_kuma=kum.prezime,
            zanimanje_kuma=kum.zanimanje,
            primedba="Примедба...",
        )
        krstenje.save()

    def handle(self, *args, **kwargs):
        parohijani = []
        for _ in range(10):
            parohijani.append(RandomUtils.create_random_parohijan(unesi_adresu, "М"))
            parohijani.append(RandomUtils.create_random_parohijan(unesi_adresu, "Ж"))

        for _ in range(5):
            RandomUtils.create_random_hram(unesi_adresu)

        for _ in range(2):
            self.create_random_svestenik()

        for parohijan in parohijani[:5]:
            self.create_random_krstenje(parohijan)

        self.stdout.write(
            self.style.SUCCESS("Успешно попуњена база података са насумичним уносима.")
        )
