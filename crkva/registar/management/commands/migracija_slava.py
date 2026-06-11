"""
Migracija tabele slava iz PostgreSQL staging tabele 'hsp_slave' u tabelu 'slave'
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import IntegrityError
from kalendar.feasts import MOVEABLE_FEAST_NAMES, upsert_moveable_feasts
from kalendar.models import Slava
from registar.management.commands.convert_utils import Konvertor


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле Слава са славама за целу годину

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_slava"
    """

    help = "Migracija tabele slava iz PostgreSQL staging tabele 'hsp_slave'"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        for uid, naziv, dan, mesec in parsed_data:
            ime = Konvertor.string(naziv)
            # Покретни празници се не уписују као фиксни (issue #259);
            # креира их upsert_moveable_feasts() из канонског списка.
            if ime in MOVEABLE_FEAST_NAMES:
                continue
            try:
                _, created = Slava.objects.get_or_create(
                    uid=uid,
                    naziv=ime,
                    opsti_naziv="",
                    dan=dan,
                    mesec=mesec,
                )

                if created:
                    created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'славе': {created_count} нових уноса."
            )
        )

        # Покретни празници Васкршњег циклуса (канонски извор истине).
        upsert_moveable_feasts(stdout=self.stdout)

        # Drop staging table after successful migration
        self._drop_staging_table()

    def _drop_staging_table(self):
        """Брише staging табелу 'hsp_slave' након успешне миграције."""
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hsp_slave")
        self.stdout.write(self.style.SUCCESS("Обрисана staging табела 'hsp_slave'."))

    def _parse_data(self):
        """
        Čita podatke iz PostgreSQL staging tabele 'hsp_slave'.
        :return: Lista parsiranih podataka (uid, naziv, dan, mesec)
        """
        parsed_data = []
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "SL_SIFRA", "SL_NAZIV", "SL_DAN", "SL_MESEC" FROM hsp_slave'
            )
            rows = cursor.fetchall()

            for row in rows:
                uid, naziv, dan, mesec = row
                parsed_data.append(
                    (
                        int(uid) if uid else 0,
                        naziv or "",
                        int(dan) if dan else 1,
                        int(mesec) if mesec else 1,
                    )
                )

        return parsed_data
