"""
Migracija tabele 'HSPSVEST.sqlite' u tabelu 'svestenici' (tabela svestenika)
"""

import sqlite3

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.management.commands.convert_utils import Konvertor
from registar.models import Parohija, Svestenik


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле svestenika

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_svestenika"
    """

    help = "'HSPSVEST.sqlite' u tabelu 'svestenici'"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        print(f"Number of parsed_data: {len(parsed_data)}")
        for svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja in parsed_data:
            try:
                broj_parohije = self._convert_roman_to_integer(parohija)
                parohija_instance, _ = Parohija.objects.get_or_create(
                    naziv=broj_parohije
                )

                ime, prezime = (ime_prezime.strip().split(" ", 1) + [""])[:2]
                svestenik = Svestenik(
                    uid=svestenik_id,
                    ime=Konvertor.string(ime),
                    prezime=Konvertor.string(prezime),
                    mesto_rodjenja="",
                    datum_rodjenja=datum_rodjenja,
                    zvanje=Konvertor.string(zvanje),
                    parohija=parohija_instance,
                )
                svestenik.save()

                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'svestenici': {created_count} нових уноса."
            )
        )

    def _convert_roman_to_integer(self, parohija):
        # Define a mapping from Roman numerals to integers
        roman_to_int = {"I": "1", "II": "2", "III": "3", "1": "1", "2": "2", "3": "3"}
        parohija = parohija.rstrip()
        converted_value = roman_to_int.get(parohija, 0)
        return converted_value

    def _parse_data(self):
        """
        Migrira tabelu HSPSVEST.sqlite
        :return: Листа парсираних података (ime_prezime, zvanje, parohija, datum_rodjenja)
        """
        parsed_data = []
        with sqlite3.connect("fixtures/combined_original_hsp_database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sv_rbr, sv_ime, sv_zvanje, sv_paroh, sv_datrod FROM HSPSVEST"
            )
            rows = cursor.fetchall()

            for row in rows:
                svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja = row
                parsed_data.append(
                    (svestenik_id, ime_prezime, zvanje, parohija, datum_rodjenja)
                )

        return parsed_data
