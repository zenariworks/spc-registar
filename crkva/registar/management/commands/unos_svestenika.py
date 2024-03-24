import random
from datetime import date

from django.core.management.base import BaseCommand
from registar.models import Parohija, Svestenik
from registar.models.svestenik import zvanja


def unesi_svestenika(
    ime: str | None = None,
    prezime: str | None = None,
    mesto_rodjenja: str | None = None,
    datum_rodjenja: str | None = None,
    zvanje: str | None = None,
    parohija: str | None = None,
):
    svestenik = Svestenik.objects.create(
        ime=ime,
        prezime=prezime,
        mesto_rodjenja=mesto_rodjenja,
        datum_rodjenja=datum_rodjenja,
        zvanje=zvanje,
        parohija=parohija or Parohija.objects.order_by("?").first(),
    )
    return svestenik


class Command(BaseCommand):
    help = "Unos sveštenika u bazu podataka."

    def add_arguments(self, parser):
        parser.add_argument(
            "broj", type=int, help="Broj sveštenika koji će biti dodati."
        )

    def handle(self, *args, **options):
        broj = options["broj"]
        for _ in range(broj):
            ime = f"Ime{_}"
            prezime = f"Prezime{_}"
            mesto_rodjenja = f"Mesto{_}"
            datum_rodjenja = date(1970 + _ % 50, (_ % 12) + 1, (_ % 28) + 1)
            zvanje = random.choice(zvanja)[0]
            svestenik = unesi_svestenika(
                ime, prezime, mesto_rodjenja, datum_rodjenja, zvanje
            )

            self.stdout.write(self.style.SUCCESS(f"Dodat sveštenik: {svestenik}"))
