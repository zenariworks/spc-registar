"""
Migracija tabele 'hspslave.sqlite' u tabelu 'slave' (са славама за целу годину)
"""
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Dan, Mesec, Slava
from registar.management.commands.convert_utils import ConvertUtils
import sqlite3


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле Слава са славама за целу годину

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_slava"
    """

    help = "'hspslave.sqlite' u tabelu 'slave'"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        for uid, naziv, dan, mesec in parsed_data:
            try:
                dan_instance, _ = Dan.objects.get_or_create(dan=dan)
                mesec_instance, _ = Mesec.objects.get_or_create(mesec=mesec)

                _, created = Slava.objects.get_or_create(
                    uid=uid,
                    naziv=ConvertUtils.latin_to_cyrillic(naziv),
                    opsti_naziv="",
                    dan=dan_instance,
                    mesec=mesec_instance,
                )

                if created:
                    created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела Слава са {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        """
        Migrira tabelu hspslave.sqlite
        :return: Листа парсираних података (uid, назив, дан, месец)
        """
        parsed_data = []
        with sqlite3.connect("fixtures/combined_original_hsp_database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sl_sifra, sl_naziv, sl_dan, sl_mesec FROM hspslave")
            rows = cursor.fetchall()

            for row in rows:
                uid, naziv, dan, mesec = row
                parsed_data.append((uid, naziv, dan, mesec))

        return parsed_data

