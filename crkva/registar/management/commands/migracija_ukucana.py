"""
Migracija tabele ukucana iz PostgreSQL staging tabele 'hsp_ukucani' u tabelu: 'ukucani'
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.convert_utils import Konvertor
from registar.models import Parohijan, Ukucanin


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'ukucani'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_ukucana"
    """

    help = "Migracija tabele ukucana iz PostgreSQL staging tabele 'hsp_ukucani'"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        # tabela 'ukucani'
        for parohijan_uid, ime_ukucana in parsed_data:
            try:
                # proveri da li postoji parohijan sa datim uid-om
                parohijan_exist = Parohijan.objects.filter(uid=parohijan_uid)
                if not parohijan_exist or ime_ukucana.rstrip() == "":
                    continue

                ukucani_instance = Ukucanin(
                    parohijan=Parohijan.objects.get(uid=parohijan_uid),
                    ime_ukucana=Konvertor.string(ime_ukucana),
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

        # Drop staging table after successful migration
        self._drop_staging_table()

    def _drop_staging_table(self):
        """Брише staging табелу 'hsp_ukucani' након успешне миграције."""
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hsp_ukucani")
        self.stdout.write(self.style.SUCCESS("Обрисана staging табела 'hsp_ukucani'."))

    def _parse_data(self):
        """
        Čita podatke iz PostgreSQL staging tabele 'hsp_ukucani'.
        :return: Lista parsiranih podataka (parohijan_uid, ime_ukucana)
        """
        parsed_data = []
        with connection.cursor() as cursor:
            cursor.execute('SELECT "UK_RBRDOM", "UK_IME" FROM hsp_ukucani')
            rows = cursor.fetchall()

            for row in rows:
                parohijan_uid, ime_ukucana = row
                parsed_data.append(
                    (
                        int(parohijan_uid) if parohijan_uid else 0,
                        ime_ukucana or "",
                    )
                )

        return parsed_data
