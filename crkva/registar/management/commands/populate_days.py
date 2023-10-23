from django.core.management.base import BaseCommand
from registar.models import Dan


class Command(BaseCommand):
    help = "Populates the Dan table with days of the month"

    def handle(self, *args, **kwargs):
        for dan in range(1, 32):
            Dan.objects.get_or_create(dan=dan)

        self.stdout.write(self.style.SUCCESS("Successfully populated Dan table"))
