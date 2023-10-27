from django.core.management.base import BaseCommand

from registar.models import Dan
from registar.models import Mesec
from registar.models import Slava


# Populate the Django model
class Command(BaseCommand):
    help = "Populates the Slavas table with slavas for the whole year"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        for name, opsti_naziv, day, month in parsed_data:
            # Retrieving or creatikrsng the respective Dan and Mesec instances
            dan_instance, _ = Dan.objects.get_or_create(dan=day)
            mesec_instance, _ = Mesec.objects.get_or_create(mesec=month)

            # Creating and saving the Slava object
            Slava.objects.create(
                naziv=name,
                opsti_naziv=opsti_naziv if opsti_naziv else "",
                dan=dan_instance,
                mesec=mesec_instance,
            )

    def _parse_data(self):
        with open("slave.sql", "r", encoding="utf-8") as file:
            raw_data = [line.strip() for line in file]

        parsed_data = []
        for entry in raw_data:
            parts = entry.split(";")

            if len(parts) == 3:
                name, opsti_naziv, date_part = parts
            elif len(parts) == 2:
                name, date_part = parts
                opsti_naziv = None  # or some default value
            else:
                # Handle other cases or raise an error
                continue

            day, month = map(int, date_part.split(","))
            parsed_data.append((name, opsti_naziv, day, month))
        return parsed_data
