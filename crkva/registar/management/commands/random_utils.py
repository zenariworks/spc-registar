# registar/management/commands/random_utils.py
import random
from datetime import date, datetime, timedelta

from django.utils import timezone
from registar.models import Hram, Narodnost, Veroispovest, Zanimanje


class RandomUtils:
    male_names = ["Никола", "Марко", "Лука", "Стефан", "Душан"]
    female_names = ["Марија", "Ана", "Јована", "Ивана", "Софија"]
    surnames = ["Јовић", "Петровић", "Николић", "Марковић", "Ђорђевић"]
    zvanja = ["јереј", "протојереј", "архијерејски намесник", "епископ"]
    parohije = ["Парохија 1", "Парохија 2", "Парохија 3", "Парохија 4"]

    @staticmethod
    def sample_occupations():
        return Zanimanje.objects.all()

    @staticmethod
    def sample_nationalities():
        return Narodnost.objects.all()

    @staticmethod
    def sample_religions():
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

        # Create a naive datetime object
        naive_datetime = datetime(year, month, day, hour, minute, second)

        # Make it timezone-aware
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
