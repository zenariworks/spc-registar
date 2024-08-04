"""
Модул команде за додавање народности у базу података према Републичком регистру.
"""

from django.core.management.base import BaseCommand
from registar.models import Narodnost


class Command(BaseCommand):
    """
    Класа Ђанго команде за додавање народности у базу података према Републичком регистру.
    """

    help = "Додавање народности у базу према Републичком регистру"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()

        for naziv in parsed_data:
            Narodnost.objects.get_or_create(naziv=naziv)

        self.stdout.write(
            self.style.SUCCESS("Успешно додате народности у базу података.")
        )

    def _parse_data(self):
        """
        Парсира податке из CSV фајла са народностима.

        :return: Листа назива народности
        """
        with open("fixtures/narodnosti.csv", "r", encoding="utf-8") as file:
            raw_data = [line.strip() for line in file]

        parsed_data = raw_data
        return parsed_data
