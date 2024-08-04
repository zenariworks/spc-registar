import random
from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from registar.management.commands.random_utils import RandomUtils
from registar.models import Adresa, Hram, Parohija, Parohijan, Svestenik, Vencanje

from .unos_adresa import unesi_adresu


class Command(BaseCommand):
    help = "Попуњава базу података насумичним парохијанима"

    male_names = ["Никола", "Марко", "Лука", "Стефан", "Душан"]
    female_names = ["Марија", "Ана", "Јована", "Ивана", "Софија"]
    surnames = ["Јовић", "Петровић", "Николић", "Марковић", "Ђорђевић"]
    zvanja = ["јереј", "протојереј", "архијерејски намесник", "епископ"]
    parohije = ["Парохија 1", "Парохија 2", "Парохија 3", "Парохија 4"]

    sample_occupations = RandomUtils.sample_occupations()
    sample_nationalities = RandomUtils.sample_nationalities()
    sample_religions = RandomUtils.sample_religions()

    def random_date_of_birth(self, min_age=0, max_age=100):
        return RandomUtils.random_date_of_birth(min_age, max_age)

    def random_datetime(self):
        return RandomUtils.random_datetime()

    def create_random_parohijan(self, gender, min_age=0) -> Parohijan:
        name = (
            random.choice(self.male_names)
            if gender == "М"
            else random.choice(self.female_names)
        )
        surname = random.choice(self.surnames)
        parohijan = Parohijan(
            ime=name,
            prezime=surname,
            mesto_rodjenja="Насумично место",
            datum_rodjenja=self.random_date_of_birth(min_age),
            vreme_rodjenja=time(random.randint(0, 23), random.randint(0, 59)),
            pol=gender,
            devojacko_prezime="" if gender == "М" else random.choice(self.surnames),
            zanimanje=random.choice(self.sample_occupations),
            veroispovest=random.choice(self.sample_religions),
            narodnost=random.choice(self.sample_nationalities),
            adresa=self.create_random_adresa(),
        )
        parohijan.save()
        return parohijan

    def random_parohijan(self, gender, min_age=0):
        """Проверава да ли постоји довољно парохијана за избор, иначе креира новог."""
        eligible_parohijan = Parohijan.objects.filter(
            pol=gender,
            datum_rodjenja__lte=date.today() - timedelta(days=min_age * 365.25),
        )
        if eligible_parohijan.exists():
            return random.choice(eligible_parohijan)
        else:
            return self.create_random_parohijan(gender, min_age)

    def get_or_create_parohija(self, naziv):
        """Враћа или креира нову парохију."""
        parohija, _ = Parohija.objects.get_or_create(naziv=naziv)
        return parohija

    def create_random_svestenik(self) -> Svestenik:
        """Креира насумичног свештеника."""
        parohije = [
            self.get_or_create_parohija("Парохија 1"),
            self.get_or_create_parohija("Парохија 2"),
            self.get_or_create_parohija("Парохија 3"),
            self.get_or_create_parohija("Парохија 4"),
        ]

        svestenik = Svestenik(
            zvanje=random.choice(self.zvanja),
            parohija=random.choice(parohije),
            ime=random.choice(self.male_names),
            prezime=random.choice(self.surnames),
            mesto_rodjenja="Насумично место",
            datum_rodjenja=self.random_date_of_birth(25),
        )
        svestenik.save()
        return svestenik

    def create_random_adresa(self) -> Adresa:
        """Креира насумичну адресу."""
        naziv_ulice = "Улица " + str(random.randint(1, 100))
        broj = str(random.randint(1, 100))
        dodatak = random.choice(["А", "Б", None])
        postkod = "11000"
        primedba = "Насумична примедба"
        naziv_mesta = "Место " + str(random.randint(1, 100))
        naziv_opstine = "Општина " + str(random.randint(1, 100))

        adresa, _ = unesi_adresu(
            naziv_ulice,
            broj,
            dodatak,
            postkod,
            primedba,
            naziv_mesta,
            naziv_opstine,
        )
        return adresa

    def create_random_hram(self):
        """Креира насумичан храм."""
        adresa = self.create_random_adresa()
        hram = Hram(
            naziv="Храм "
            + random.choice(
                ["Светог Саве", "Светог Николе", "Светог Марка", "Свете Петке"]
            ),
            adresa=adresa,
        )
        hram.save()
        return hram

    def create_random_vencanje(self):
        """Креира насумично венчање."""
        zenik = self.random_parohijan("М", 18)
        nevesta = self.random_parohijan("Ж", 18)

        hram = self.create_random_hram()
        svestenik = self.create_random_svestenik()

        vencanje = Vencanje(
            knjiga=random.randint(1, 100),
            strana=random.randint(1, 500),
            tekuci_broj=random.randint(1, 1000),
            datum=self.random_datetime().date(),
            zenik=zenik,
            zenik_rb_brak=random.randint(1, 3),
            nevesta=nevesta,
            nevesta_rb_brak=random.randint(1, 3),
            hram=hram,
            svestenik=svestenik,
            datum_ispita=self.random_datetime().date(),
            primedba="Насумична примедба...",
        )
        vencanje.save()

    def handle(self, *args, **kwargs):
        """Рукује креирањем насумичних података."""
        for _ in range(10):
            self.create_random_vencanje()

        self.stdout.write(
            self.style.SUCCESS("Успешно попуњена база података са насумичним подацима")
        )
