"""
Модул са помоћним функцијама за генерисање насумичних података.
"""

import random
from datetime import date, datetime, time, timedelta

from django.utils import timezone
from registar.models import Hram, Narodnost, Parohijan, Veroispovest, Zanimanje


class RandomUtils:
    """
    Класа која садржи статичке методе за генерисање насумичних података за различите моделе.
    """

    male_names = ["Никола", "Марко", "Лука", "Стефан", "Душан"]
    female_names = ["Марија", "Ана", "Јована", "Ивана", "Софија"]
    surnames = ["Јовић", "Петровић", "Николић", "Марковић", "Ђорђевић"]
    zvanja = ["јереј", "протојереј", "архијерејски намесник", "епископ"]
    parohije = ["Парохија 1", "Парохија 2", "Парохија 3", "Парохија 4"]

    @staticmethod
    def sample_occupations():
        """Враћа све доступне занимања."""
        return Zanimanje.objects.all()

    @staticmethod
    def sample_nationalities():
        """Враћа све доступне народности."""
        return Narodnost.objects.all()

    @staticmethod
    def sample_religions():
        """Враћа све доступне вероисповести."""
        return Veroispovest.objects.all()

    @staticmethod
    def random_date_of_birth(min_age=0, max_age=100):
        """Генерише насумичан датум рођења."""
        today = date.today()
        start_date = today - timedelta(days=max_age * 365.25)
        end_date = today - timedelta(days=min_age * 365.25)
        random_days = random.randint(0, (end_date - start_date).days)
        return start_date + timedelta(days=random_days)

    @staticmethod
    def random_datetime():
        """Генерише насумичан датум и време."""
        year = random.randint(2000, 2022)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Да избегнемо крај месеца
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        # Креирање наивног објекта datetime
        naive_datetime = datetime(year, month, day, hour, minute, second)

        # Претварање у објекат свестан временске зоне
        aware_datetime = timezone.make_aware(
            naive_datetime, timezone.get_default_timezone()
        )
        return aware_datetime

    @staticmethod
    def create_random_adresa(unesi_adresu):
        """Креира насумичну адресу."""
        naziv_ulice = "Улица " + str(random.randint(1, 100))
        broj = str(random.randint(1, 100))
        dodatak = random.choice(["А", "Б", None])
        postkod = "11000"
        primedba = "Насумична примедба"
        naziv_mesta = "Место " + str(random.randint(1, 100))
        naziv_opstine = "Општина " + str(random.randint(1, 100))

        adresa, _ = unesi_adresu(
            naziv_ulice,
            broj,
            dodatak,
            postkod,
            primedba,
            naziv_mesta,
            naziv_opstine,
        )
        return adresa

    @staticmethod
    def create_random_hram(unesi_adresu):
        """Креира насумичан објекат Hram."""
        adresa = RandomUtils.create_random_adresa(unesi_adresu)
        hram = Hram(
            naziv="Храм "
            + random.choice(
                ["Светог Саве", "Светог Николе", "Светог Марка", "Свете Петке"]
            ),
            adresa=adresa,
        )
        hram.save()
        return hram

    @staticmethod
    def create_random_parohijan(unesi_adresu, gender, min_age=0) -> Parohijan:
        """Креира насумичног парохијана."""
        name = (
            random.choice(RandomUtils.male_names)
            if gender == "М"
            else random.choice(RandomUtils.female_names)
        )
        surname = random.choice(RandomUtils.surnames)
        parohijan = Parohijan(
            ime=name,
            prezime=surname,
            mesto_rodjenja="Насумично место",
            datum_rodjenja=RandomUtils.random_date_of_birth(min_age),
            vreme_rodjenja=time(random.randint(0, 23), random.randint(0, 59)),
            pol=gender,
            devojacko_prezime=(
                "" if gender == "М" else random.choice(RandomUtils.surnames)
            ),
            zanimanje=random.choice(RandomUtils.sample_occupations()),
            veroispovest=random.choice(RandomUtils.sample_religions()),
            narodnost=random.choice(RandomUtils.sample_nationalities()),
            adresa=RandomUtils.create_random_adresa(unesi_adresu),
        )
        parohijan.save()
        return parohijan
