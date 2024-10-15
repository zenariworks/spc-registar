"""
Migracija tabele `HSPUKUCANI.sqlite` (tabela ukucana) u tabelu: `ukucani`
"""
import sqlite3
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Ukucanin, Parohijan
from registar.management.commands.convert_utils import ConvertUtils


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'parohijani'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_ukucana"
    """
    help = "Migracija tabele `HSPUKUCANI.sqlite` (tabela ukucana) u tabelu: `ukucani`"

    def handle(self, *args, **kwargs):

        parsed_data = self._parse_data()
        created_count = 0

        # tabela 'ukucani'
        for parohijan_uid, ime_ukucana in parsed_data:
            try:
                # test
                #print("parohijan_uid: " + str(parohijan_uid))
                # proveri da li postoji parohijan sa datim uid-om
                parohijan_exist = Parohijan.objects.filter(uid=parohijan_uid)
                #print("parohijan_exist: " + str(parohijan_exist))
                #print("ime_ukucana: " + str(ime_ukucana))
                if not parohijan_exist or ime_ukucana.rstrip() == "":
                    continue

                ukucani_instance = Ukucanin(
                    parohijan=Parohijan.objects.get(uid=parohijan_uid),
                    ime_ukucana=ConvertUtils.latin_to_cyrillic(ime_ukucana)
                )
                ukucani_instance.save()

                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табеле 'укућани': {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        """
        Migracija tabele 'HSPDOMACINI.sqlite' 
            uk_rbrdom       - parohijan_uid, 
            uk_ime          - ime_ukucana

        :return: Листа парсираних података (parohijan_uid, ime_ukucana)
        """
        parsed_data = []
        with sqlite3.connect("fixtures/combined_original_hsp_database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uk_rbrdom, uk_ime FROM HSPUKUCANI")
            #cursor.execute("SELECT uk_rbrdom, uk_ime FROM HSPUKUCANI where uk_rbrdom=1831")
            rows = cursor.fetchall()

            for row in rows:
                parohijan_uid, ime_ukucana = row
                parsed_data.append((parohijan_uid, ime_ukucana))

        return parsed_data

