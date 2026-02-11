"""
Migracija podataka iz PostgreSQL staging tabele 'hsp_ulice' u tabele 'opstine', 'mesta', i 'ulice'.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.convert_utils import Konvertor
from registar.models import Mesto, Ulica
from registar.models.opstina import Opstina

from .unos_drzava import unesi_drzavu


class Command(BaseCommand):
    """
    Django команда за попуњавање табела 'opstine', 'mesta', и 'ulice'.

    Коришћење:
    docker compose run --rm app sh -c "python manage.py migracija_ulica"
    """

    help = "Migracija podataka iz PostgreSQL staging tabele 'hsp_ulice'"

    def handle(self, *args, **kwargs):
        """Главна метода која обрађује миграцију података."""
        opstina = self._get_or_create_opstina("Чукарица")
        mesto = self._get_or_create_mesto("Чукарица")
        drzava = self._get_or_create_drzava("Србија")

        podaci = self._obradi_podatke()
        broj_unetih = self._unos_ulica(podaci, drzava, mesto, opstina)

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'ulice': {broj_unetih} нових уноса."
            )
        )

        # Drop staging table after successful migration
        self._drop_staging_table()

    def _drop_staging_table(self):
        """Брише staging табелу 'hsp_ulice' након успешне миграције."""
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hsp_ulice")
        self.stdout.write(self.style.SUCCESS("Обрисана staging табела 'hsp_ulice'."))

    def _get_or_create_opstina(self, naziv):
        """Враћа инстанцу 'Opstina', креира је ако не постоји."""
        return Opstina.objects.get_or_create(naziv=naziv)[0]

    def _get_or_create_mesto(self, naziv):
        """Враћа инстанцу 'Mesto', креира је ако не постоји."""
        return Mesto.objects.get_or_create(naziv=naziv)[0]

    def _get_or_create_drzava(self, naziv):
        """Враћа инстанцу 'Drzava', креира је ако не постоји."""
        return unesi_drzavu(naziv)[0]

    def _obradi_podatke(self):
        """Čita podatke iz PostgreSQL staging tabele 'hsp_ulice'."""
        with connection.cursor() as cursor:
            cursor.execute('SELECT "UL_SIFRA", "UL_NAZIV", "UL_RBRSV" FROM hsp_ulice')
            rows = cursor.fetchall()
            return [
                (
                    int(row[0]) if row[0] else 0,
                    row[1] or "",
                    int(row[2]) if row[2] else 0,
                )
                for row in rows
            ]

    def _unos_ulica(self, podaci, drzava, mesto, opstina):
        """Креира уносе у табели 'ulice' на основу парсираних података."""
        return sum(
            self._unos_ulice(id, naziv, svestenik_id, drzava, mesto, opstina)
            for id, naziv, svestenik_id in podaci
            if naziv and naziv.strip()
        )

    def _unos_ulice(self, id, naziv, svestenik_id, drzava, mesto, opstina):
        """Креира једну улицу и враћа 1 ако је успешно креирана, иначе 0."""
        try:
            Ulica.objects.create(
                uid=id,
                naziv=Konvertor.string(naziv.strip()),
                drzava_id=drzava.uid,
                mesto_id=mesto.uid,
                opstina_id=opstina.uid,
                svestenik_id=svestenik_id,
            )
            return 1
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Грешка при креирању уноса за улицу '{naziv.strip()}': {e}"
                )
            )
            return 0
