"""
Migracija tabele `HSPKRST.sqlite` (tabele krstenja) u tabelu 'krstenja'
"""
import sqlite3
import uuid
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from registar.management.commands.random_utils import RandomUtils
from registar.models import Hram, Krstenje, Parohija, Parohijan, Svestenik

from .unos_adresa import unesi_adresu

class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'krstenja'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_krstenja"

    k_proknj --> Krstenje.knjiga
    k_protst --> Krstenje.strana

    k_iz + k_ulica

    k_rodjgod + k_rodmese + k_rodjdan --> Krstenje.dete <= Parohijan.datum_rodjenja
    k_rodjvre --> Krstenje.dete <= Parohijan.vreme_rodjenja
    k_rodjmesto --> Krstenje.dete <= Parohijan.mesto_rodjena
    k_rodjopst -->
    """
    help = "Migracija tabele `HSPKRST.sqlite` (tabele krstenja) u tabelu 'krstenja'"

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

    def create_random_krstenje(self, parohijan):
        """Креира насумично крштење."""
        dete = self.random_parohijan("М" if random.choice([True, False]) else "Ж")
        otac = self.random_parohijan("М", min_age=20)
        majka = self.random_parohijan("Ж", min_age=20)
        kum = self.random_parohijan(
            "М" if random.choice([True, False]) else "Ж", min_age=20
        )
        svestenik = self.create_random_svestenik()
        hram = Hram.objects.order_by("?").first()

        krstenje = Krstenje(
            knjiga=random.randint(1, 100),
            strana=random.randint(1, 500),
            tekuci_broj=random.randint(1, 1000),
            datum=RandomUtils.random_datetime().date(),
            vreme=RandomUtils.random_datetime().time(),
            hram=hram,
            dete=dete,
            dete_majci=random.randint(1, 10),
            dete_bracno=random.choice([True, False]),
            mana=random.choice([True, False]),
            blizanac=self.random_parohijan(
                "М" if random.choice([True, False]) else "Ж"
            ),
            otac=otac,
            majka=majka,
            svestenik=svestenik,
            kum=kum,
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

#
# class Command(BaseCommand):
#     """
#     Класа Ђанго команде за попуњавање базе података насумичним парохијанима.
#     """

#     help = "Попуњава базу података насумичним парохијанима"

#     def random_parohijan(self, gender, min_age=0):
#         """Креира насумично парохијана."""
#         eligible_parohijan = Parohijan.objects.filter(
#             pol=gender,
#             datum_rodjenja__lte=date.today() - timedelta(days=min_age * 365.25),
#         )
#         if eligible_parohijan.exists():
#             return random.choice(eligible_parohijan)
#         else:
#             return RandomUtils.create_random_parohijan(unesi_adresu, gender, min_age)

#     def get_or_create_parohija(self, naziv):
#         """Креира насумично парохију."""
#         parohija, _ = Parohija.objects.get_or_create(naziv=naziv)
#         return parohija

#     def create_random_svestenik(self) -> Svestenik:
#         """Креира насумично свештеника."""
#         parohije = [
#             self.get_or_create_parohija("Парохија 1"),
#             self.get_or_create_parohija("Парохија 2"),
#             self.get_or_create_parohija("Парохија 3"),
#             self.get_or_create_parohija("Парохија 4"),
#         ]

#         svestenik = Svestenik(
#             zvanje=random.choice(RandomUtils.zvanja),
#             parohija=random.choice(parohije),
#             ime=random.choice(RandomUtils.male_names),
#             prezime=random.choice(RandomUtils.surnames),
#             mesto_rodjenja="Насумично место",
#             datum_rodjenja=RandomUtils.random_date_of_birth(25),
#         )
#         svestenik.save()
#         return svestenik

#     def create_random_krstenje(self, parohijan):
#         """Креира насумично крштење."""
#         dete = self.random_parohijan("М" if random.choice([True, False]) else "Ж")
#         otac = self.random_parohijan("М", min_age=20)
#         majka = self.random_parohijan("Ж", min_age=20)
#         kum = self.random_parohijan(
#             "М" if random.choice([True, False]) else "Ж", min_age=20
#         )
#         svestenik = self.create_random_svestenik()
#         hram = Hram.objects.order_by("?").first()

#         krstenje = Krstenje(
#             knjiga=random.randint(1, 100),
#             strana=random.randint(1, 500),
#             tekuci_broj=random.randint(1, 1000),
#             datum=RandomUtils.random_datetime().date(),
#             vreme=RandomUtils.random_datetime().time(),
#             hram=hram,
#             dete=dete,
#             dete_majci=random.randint(1, 10),
#             dete_bracno=random.choice([True, False]),
#             mana=random.choice([True, False]),
#             blizanac=self.random_parohijan(
#                 "М" if random.choice([True, False]) else "Ж"
#             ),
#             otac=otac,
#             majka=majka,
#             svestenik=svestenik,
#             kum=kum,
#             primedba="Примедба...",
#         )
#         krstenje.save()

#     def handle(self, *args, **kwargs):
#         parohijani = []
#         for _ in range(10):
#             parohijani.append(RandomUtils.create_random_parohijan(unesi_adresu, "М"))
#             parohijani.append(RandomUtils.create_random_parohijan(unesi_adresu, "Ж"))

#         for _ in range(5):
#             RandomUtils.create_random_hram(unesi_adresu)

#         for _ in range(2):
#             self.create_random_svestenik()

#         for parohijan in parohijani[:5]:
#             self.create_random_krstenje(parohijan)

#         self.stdout.write(
#             self.style.SUCCESS("Успешно попуњена база података са насумичним уносима.")
#         )
