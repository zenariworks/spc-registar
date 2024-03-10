# registar/management/commands/random_utils.py

import random
from datetime import date, datetime, timedelta

from django.utils import timezone
from registar.models import Narodnost, Veroispovest, Zanimanje


class RandomUtils:
    male_names = ["Никола", "Марко", "Лука", "Стефан", "Душан"]
    female_names = ["Марија", "Ана", "Јована", "Ивана", "Софија"]
    surnames = ["Јовић", "Петровић", "Николић", "Марковић", "Ђорђевић"]
    zvanja = ["јереј", "протојереј", "архијерејски намесник", "епископ"]
    sample_occupations = Zanimanje.objects.all()
    sample_nationalities = Narodnost.objects.all()
    sample_religions = Veroispovest.objects.all()

    @staticmethod
    def random_date_of_birth(min_age=0, max_age=100):
        today = date.today()
        start_date = today - timedelta(days=max_age * 365.25)
        end_date = today - timedelta(days=min_age * 365.25)
        random_days = random.randint(0, (end_date - start_date).days)
        return start_date + timedelta(days=random_days)

    @staticmethod
    def random_datetime():
        year = random.randint(2000, 2022)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        naive_datetime = datetime(year, month, day, hour, minute, second)
        return timezone.make_aware(naive_datetime, timezone.get_default_timezone())

    # Add other shared methods like create_random_parohijan, create_random_svestenik, etc.
