from django.core.management.base import BaseCommand
from registar.models import Mesec

class Command(BaseCommand):
    help = "Попуњава табелу Месец са месецима и њиховим називима на српском ћирилицом"

    def handle(self, *args, **kwargs):
        meseci = {
            1: "јануар",
            2: "фебруар",
            3: "март",
            4: "април",
            5: "мај",
            6: "јун",
            7: "јул",
            8: "август",
            9: "септембар",
            10: "октобар",
            11: "новембар",
            12: "децембар",
        }

        for redni_broj, naziv in meseci.items():
            Mesec.objects.get_or_create(mesec=redni_broj, naziv=naziv)

        self.stdout.write(
            self.style.SUCCESS(
                "Успешно попуњена табела Месец са називима месеци на српском ћирилицом"
            )
        )
