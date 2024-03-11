from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Veroispovest


class Command(BaseCommand):
    help = "Додавање вероисповести у базу према Републичком регистру"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        for naziv in parsed_data:
            try:
                _, created = Veroispovest.objects.get_or_create(naziv=naziv)
                if created:
                    created_count += 1
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно додате вероисповести у базу података: {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        try:
            with open(r"fixtures/veroispovesti.csv", "r", encoding="utf-8") as file:
                raw_data = [line.strip() for line in file]
            return raw_data
        except IOError as e:
            self.stdout.write(self.style.ERROR(f"Грешка при читању датотеке: {e}"))
            return []
