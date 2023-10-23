from django.core.management.base import BaseCommand

from registar.models import Zanimanje


class Command(BaseCommand):
    help = "Додавање занимања у базу према Републичком регистру"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()

        for sifra, naziv in parsed_data:
            Zanimanje.objects.create(
                sifra=sifra,
                naziv=naziv,
            )

    def _parse_data(self):
        with open("zanimanja.csv", "r", encoding="utf-8") as file:
            raw_data = [line.strip() for line in file]

        parsed_data = []
        for unos in raw_data:
            sifra, naziv = unos.split(";")
            parsed_data.append((sifra, naziv))

        return parsed_data
