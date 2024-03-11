from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Zanimanje


class Command(BaseCommand):
    help = "Додавање занимања у базу према Републичком регистру"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        for sifra, naziv in parsed_data:
            try:
                _, created = Zanimanje.objects.get_or_create(sifra=sifra, naziv=naziv)
                if created:
                    created_count += 1
            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(f"Грешка при креирању занимања: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно додата занимања у базу података: {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        try:
            with open("fixtures/zanimanja.csv", "r", encoding="utf-8") as file:
                raw_data = [line.strip() for line in file]
        except IOError as e:
            self.stdout.write(self.style.ERROR(f"Грешка при читању датотеке: {e}"))
            return []

        parsed_data = []
        for unos in raw_data:
            try:
                sifra, naziv = unos.split(";")
                parsed_data.append((sifra, naziv))
            except ValueError as e:
                self.stdout.write(self.style.ERROR(f"Грешка у формату података: {e}"))

        return parsed_data
