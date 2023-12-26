# registar/management/commands/unos_random.py

import random
from datetime import date, time, timedelta, datetime

from django.utils import timezone
from django.core.management.base import BaseCommand
from registar.models import (
    Osoba, Zanimanje, Narodnost,
    Veroispovest, Svestenik, Krstenje,
    Adresa, Hram
    )


class Command(BaseCommand):
    help = 'Populates the database with random Osoba instances'

    # Serbian names and surnames in Cyrillic
    male_names = ["Никола", "Марко", "Лука", "Стефан", "Душан"]
    female_names = ["Марија", "Ана", "Јована", "Ивана", "Софија"]
    surnames = ["Јовић", "Петровић", "Николић", "Марковић", "Ђорђевић"]

    # Sample zvanja and parohija
    zvanja = ["јереј", "протојереј", "архијерејски намесник", "епископ"]
    parohije = ["Парохија 1", "Парохија 2", "Парохија 3", "Парохија 4"]  # Replace with actual parohija names

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
        aware_datetime = timezone.make_aware(naive_datetime, timezone.get_default_timezone())
        return aware_datetime

    def create_random_osoba(self, gender, min_age=0):
        name = random.choice(self.male_names) if gender == "М" else random.choice(self.female_names)
        surname = random.choice(self.surnames)
        osoba = Osoba(
            ime=name,
            prezime=surname,
            mesto_rodjenja="Random Mesto",
            datum_rodjenja=self.random_date_of_birth(min_age),
            vreme_rodjenja=time(random.randint(0, 23), random.randint(0, 59)),
            pol=gender,
            devojacko_prezime="" if gender == "М" else "Random Devojacko",
            zanimanje=random.choice(self.sample_occupations),
            veroispovest=random.choice(self.sample_religions),
            narodnost=random.choice(self.sample_nationalities),
            adresa="Random Adresa"
        )
        osoba.save()
        return osoba

    def get_or_create_random_osoba(self, gender, min_age=0):
        # Check if there are enough Osoba instances to choose from
        eligible_osoba = Osoba.objects.filter(
            pol=gender,
            datum_rodjenja__lte=date.today() - timedelta(days=min_age * 365.25)
        )
        if eligible_osoba.exists():
            return random.choice(eligible_osoba)
        else:
            return self.create_random_osoba(gender, min_age)

    def create_random_svestenik(self):
        # Ensure the svestenik is older than 25 years
        osoba = self.get_or_create_random_osoba("М", min_age=25)
        svestenik = Svestenik(
            zvanje=random.choice(self.zvanja),
            parohija=random.choice(self.parohije),
            osoba=osoba  # Associate the created Osoba instance
        )
        svestenik.save()
        return svestenik

    def create_random_adresa(self):
        adresa = Adresa(
            ulica="Улица " + str(random.randint(1, 100)),
            mesto="Место " + str(random.randint(1, 100)),
            opstina="Општина " + str(random.randint(1, 100)),
            postanski_broj=str(random.randint(10000, 99999)),
            drzava="Србија"
        )
        adresa.save()
        return adresa

    def create_random_hram(self):
        adresa = self.create_random_adresa()
        hram = Hram(
            naziv="Храм " + random.choice(["Светог Саве", "Светог Николе", "Светог Марка", "Свете Петке"]),
            adresa=adresa
        )
        hram.save()
        return hram

    def create_random_krstenje(self, osoba):
        # Create random persons for different roles
        dete = self.get_or_create_random_osoba("М" if random.choice([True, False]) else "Ж")
        otac = self.get_or_create_random_osoba("М", min_age=20)
        majka = self.get_or_create_random_osoba("Ж", min_age=20)
        kum = self.get_or_create_random_osoba("М" if random.choice([True, False]) else "Ж", min_age=20)
        svestenik = self.create_random_svestenik()
        hram = Hram.objects.order_by('?').first()  # Get a random Hram instance

        krstenje = Krstenje(
            knjiga=random.randint(1, 100),  # Assuming this is a random number
            strana=random.randint(1, 500),
            tekuci_broj=random.randint(1, 1000),
            datum=self.random_datetime().date(),
            vreme=self.random_datetime().time(),
            hram=hram,
            dete=dete,
            dete_majci=random.randint(1, 10),
            dete_bracno=random.choice([True, False]),
            mana=random.choice([True, False]),
            blizanac=self.get_or_create_random_osoba("М" if random.choice([True, False]) else "Ж"),  # Assuming a random Osoba
            otac=otac,
            majka=majka,
            svestenik=svestenik,
            kum=kum,
            primedba="Random Primedba"
        )
        krstenje.save()


    def handle(self, *args, **kwargs):
        # Create 10 male and 10 female Osoba instances
        osobe = []
        for _ in range(10):
            osobe.append(self.create_random_osoba("М"))
            osobe.append(self.create_random_osoba("Ж"))

        # Create a few Hram instances
        for _ in range(5):
            self.create_random_hram()

        # Create 2 Svestenik instances
        for _ in range(2):
            self.create_random_svestenik()

        # Create at least 5 Krstenje instances using the first 5 Osoba instances
        for osoba in osobe[:5]:
            self.create_random_krstenje(osoba)

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with random instances'))
