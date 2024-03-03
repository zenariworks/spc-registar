# registar/management/commands/unos_random.py

import random
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from registar.models import (
    Adresa,
    Hram,
    Vencanje,
    Narodnost,
    Parohija,
    Parohijan,
    Svestenik,
    Veroispovest,
    Zanimanje,
)


class Command(BaseCommand):
    help = "Populates the database with random parohijan instances"

    # Serbian names and surnames in Cyrillic
    male_names = ["Никола", "Марко", "Лука", "Стефан", "Душан"]
    female_names = ["Марија", "Ана", "Јована", "Ивана", "Софија"]
    surnames = ["Јовић", "Петровић", "Николић", "Марковић", "Ђорђевић"]

    # Sample zvanja and parohija
    zvanja = ["јереј", "протојереј", "архијерејски намесник", "епископ"]
    parohije = [
        "Парохија 1",
        "Парохија 2",
        "Парохија 3",
        "Парохија 4",
    ]  # Replace with actual parohija names

    # Sample data pools
    sample_occupations = Zanimanje.objects.all()
    sample_nationalities = Narodnost.objects.all()
    sample_religions = Veroispovest.objects.all()

    def random_date_of_birth(self, min_age=0, max_age=100):
        today = date.today()
        start_date = today - timedelta(days=max_age * 365.25)
        end_date = today - timedelta(days=min_age * 365.25)
        random_days = random.randint(0, (end_date - start_date).days)
        return start_date + timedelta(days=random_days)

    def random_datetime(self):
        year = random.randint(2000, 2022)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # To avoid month-end complexities
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        # Create a naive datetime object
        naive_datetime = datetime(year, month, day, hour, minute, second)

        # Make it timezone-aware
        aware_datetime = timezone.make_aware(
            naive_datetime, timezone.get_default_timezone()
        )
        return aware_datetime

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
            adresa="Насумична адреса",
        )
        parohijan.save()
        return parohijan

    def random_parohijan(self, gender, min_age=0):
        # Check if there are enough parohijan instances to choose from
        eligible_parohijan = Parohijan.objects.filter(
            pol=gender,
            datum_rodjenja__lte=date.today() - timedelta(days=min_age * 365.25),
        )
        if eligible_parohijan.exists():
            return random.choice(eligible_parohijan)
        else:
            return self.create_random_parohijan(gender, min_age)

    def get_or_create_parohija(self, naziv):
        parohija, created = Parohija.objects.get_or_create(naziv=naziv)
        return parohija

    def create_random_svestenik(self) -> Svestenik:
        parohije = [
            self.get_or_create_parohija("Парохија 1"),
            self.get_or_create_parohija("Парохија 2"),
            self.get_or_create_parohija("Парохија 3"),
            self.get_or_create_parohija("Парохија 4"),
        ]

        svestenik = Svestenik(
            zvanje=random.choice(self.zvanja),
            parohija=random.choice(parohije),  # Use an actual Parohija instance
            ime=random.choice(self.male_names),
            prezime=random.choice(seq=self.surnames),
            mesto_rodjenja="Насумично место",
            datum_rodjenja=self.random_date_of_birth(25),
        )
        svestenik.save()
        return svestenik

    def create_random_adresa(self) -> Adresa:
        adresa = Adresa(
            ulica="Улица " + str(random.randint(1, 100)),
            mesto="Место " + str(random.randint(1, 100)),
            opstina="Општина " + str(random.randint(1, 100)),
            postanski_broj=str(random.randint(10000, 99999)),
            drzava="Србија",
        )
        adresa.save()
        return adresa

    def create_random_hram(self):
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
        # Ensure there are male and female parohijani available or create them
        zenik = self.random_parohijan("М", 18)
        nevesta = self.random_parohijan("Ж", 18)

        # Create or get a random hram and svestenik
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
            napomena="Насумична напомена...",
        )
        vencanje.save()

    def handle(self, *args, **kwargs):
        for i in range(10):
            self.create_random_vencanje()

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully populated the database with random instances"
            )
        )
