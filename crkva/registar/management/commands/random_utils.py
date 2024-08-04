# registar/management/commands/random_utils.py
import random
from datetime import date, datetime, timedelta

from django.utils import timezone
from registar.models import Narodnost, Veroispovest, Zanimanje


class RandomUtils:
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
        """Генерише насумично датум и време."""
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
    def sample_occupations():
        """Генерише насумично занимање."""
        return Zanimanje.objects.all()

    @staticmethod
    def sample_nationalities():
        """Генерише насумично националност."""
        return Narodnost.objects.all()

    @staticmethod
    def sample_religions():
        """Генерише насумично вероисповест."""
        return Veroispovest.objects.all()
