from django.core.management.base import BaseCommand
from registar.models import Mesec
from registar.utils import GREGORIAN_MONTHS


class Command(BaseCommand):
    help = "Попуњава табелу Месец са месецима и њиховим називима на српском ћирилицом"

    def handle(self, *args, **kwargs):
        meseci = GREGORIAN_MONTHS

        for redni_broj, naziv in meseci.items():
            Mesec.objects.get_or_create(mesec=redni_broj, naziv=naziv)

        self.stdout.write(
            self.style.SUCCESS(
                "Успешно попуњена табела Месец са називима месеци на српском ћирилицом"
            )
        )
