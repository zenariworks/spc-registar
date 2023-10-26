from django.core.management.base import BaseCommand

from registar.models import Veroispovest


class Command(BaseCommand):
    help = "Додавање занимања у базу према Републичком регистру"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()

        for naziv in parsed_data:
            Veroispovest.objects.create(
                naziv=naziv,
            )

    def _parse_data(self):
        with open("veroispovesti.csv", "r", encoding="utf-8") as file:
            raw_data = [line.strip() for line in file]

        parsed_data = raw_data
        return parsed_data
