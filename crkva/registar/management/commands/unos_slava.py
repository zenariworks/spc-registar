"""
Модул команде за попуњавање табеле Слава са славама за целу годину.
"""

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Dan, Mesec, Slava


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле Слава са славама за целу годину.
    """

    help = "Попуњава табелу Слава са славама за целу годину"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        for name, opsti_naziv, day, month in parsed_data:
            try:
                dan_instance, _ = Dan.objects.get_or_create(dan=day)
                mesec_instance, _ = Mesec.objects.get_or_create(mesec=month)

                _, created = Slava.objects.get_or_create(
                    naziv=name,
                    opsti_naziv=opsti_naziv if opsti_naziv else "",
                    dan=dan_instance,
                    mesec=mesec_instance,
                )

                if created:
                    created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела Слава са {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        """
        Парсира податке из SQL фајла са славама.

        :return: Листа парсираних података (назив, општи назив, дан, месец)
        """
        with open("fixtures/slave.sql", "r", encoding="utf-8") as file:
            raw_data = [line.strip() for line in file]

        parsed_data = []
        for entry in raw_data:
            parts = entry.split(";")

            if len(parts) == 3:
                name, opsti_naziv, date_part = parts
            elif len(parts) == 2:
                name, date_part = parts
                opsti_naziv = None
            else:
                continue

            day, month = map(int, date_part.split(","))
            parsed_data.append((name, opsti_naziv, day, month))
        return parsed_data
