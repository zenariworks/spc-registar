"""
Migracija tabele 'HSPDOMACINI.sqlite' u tabele 'opstine', 'mesta', 'ulice', 'adrese'
"""

import sqlite3
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Ulica
from registar.models.opstina import Opstina
from registar.models import Mesto
#from registar.models.svestenik import zvanja
from registar.management.commands.convert_utils import Konvertor
from .unos_drzava import unesi_drzavu


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'opstine', 'mesta', 'ulice'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_ulica"
    """

    help = "'HSPULICE.sqlite' u tabele 'opstine', 'mesta', 'drzave', 'ulice'"

    def handle(self, *args, **kwargs):

        # tabela 'opstine': Cukarica, Srbija
        opstina_instance, _ = Opstina.objects.get_or_create(naziv="Чукарица")

        # tabela 'mesta': Cukarica
        mesto_instance, _ =  Mesto.objects.get_or_create(naziv="Чукарица")

        # drzava_id 
        drzava_instance, _ = unesi_drzavu("Србија")

        # Output the uids
        #print("opstina UID:", opstina_instance.uid)
        #print("mesto UID:", mesto_instance.uid)
        #print("drzava UID:", drzava_instance.uid)
       
        parsed_data_streets = self._parse_data()
        created_count = 0

        for ulice_id, naziv_ulice, svestenik_id in parsed_data_streets:
            try:
                ulica = Ulica(
                    uid=ulice_id,
                    naziv=Konvertor.string(naziv_ulice),
                    drzava_id=drzava_instance.uid,
                    mesto_id=mesto_instance.uid,
                    opstina_id=opstina_instance.uid,
                    svestenik_id=svestenik_id
                )
                ulica.save()

                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'ulice': {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        """
        Migracija tabele 'HSPULICE.sqlite' u tabele 'opstine', 'mesta', 'ulice'
        :return: Листа парсираних података (ulice_id, naziv_ulice, svestenik_id)
        """
        parsed_data = []
        with sqlite3.connect("fixtures/combined_original_hsp_database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ul_sifra, ul_naziv, ul_rbrsv FROM HSPULICE")
            rows = cursor.fetchall()

            for row in rows:
                ulice_id, naziv_ulice, svestenik_id = row
                parsed_data.append((ulice_id, naziv_ulice, svestenik_id))

        return parsed_data

