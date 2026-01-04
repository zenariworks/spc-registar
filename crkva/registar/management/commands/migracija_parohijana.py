"""
Migracija tabele domacina iz PostgreSQL staging tabele 'hsp_domacini' u tabele: 'adresa', 'parohijani'
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.convert_utils import Konvertor
from registar.models import Adresa, Parohijan, Slava, Ulica


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'parohijani'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_parohijana"
    """

    help = "Migracija tabele domacina iz PostgreSQL staging tabele 'hsp_domacini'"

    def handle(self, *args, **kwargs):
        parsed_data = self._parse_data()
        created_count = 0

        for (
            parohijan_uid,
            ime_prezime,
            ulica_uid,
            broj_ulice,
            oznaka_ulice,
            broj_stana,
            telefon_fiksni,
            telefon_mobilni,
            slava_uid,
            slavska_vodica,
            uskrsnja_vodica,
            napomena,
        ) in parsed_data:
            try:
                if ulica_uid is None or ulica_uid == 0:
                    continue

                adresa_instance = Adresa(
                    broj=broj_ulice,
                    sprat=None,
                    broj_stana=broj_stana,
                    dodatak=Konvertor.string(oznaka_ulice),
                    postkod=None,
                    primedba=Konvertor.string(napomena),
                    ulica=Ulica.objects.get(uid=ulica_uid),
                )
                adresa_instance.save()

                ime, prezime = (ime_prezime.strip().split(" ", 1) + [""])[:2]
                parohijan = Parohijan(
                    uid=parohijan_uid,
                    ime=Konvertor.string(ime),
                    prezime=Konvertor.string(prezime),
                    adresa=adresa_instance,
                    slava=Slava.objects.get(uid=slava_uid),
                    tel_fiksni=telefon_fiksni,
                    tel_mobilni=telefon_mobilni,
                    slavska_vodica=True if slavska_vodica.rstrip() == "D" else False,
                    uskrsnja_vodica=True if uskrsnja_vodica.rstrip() == "D" else False,
                    mesto_rodjenja=None,
                    datum_rodjenja=None,
                    vreme_rodjenja=None,
                    pol=None,
                    devojacko_prezime=None,
                    zanimanje=None,
                    veroispovest=None,
                    narodnost=None,
                )
                parohijan.save()

                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњене табеле 'адресе' и 'парохијани': {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        """
        Čita podatke iz PostgreSQL staging tabele 'hsp_domacini'.
        :return: Lista parsiranih podataka
        """
        parsed_data = []
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT "DOM_RBR", "DOM_IME", "DOM_RBRUL", "DOM_BROJ", "DOM_OZNAKA", "DOM_STAN",
                          "DOM_TELDIR", "DOM_TELMOB", "DOM_RBRSL", "DOM_SLAVOD", "DOM_USKVOD", "DOM_NAPOM"
                   FROM hsp_domacini"""
            )
            rows = cursor.fetchall()

            for row in rows:
                (
                    parohijan_uid,
                    ime_prezime,
                    ulica_uid,
                    broj_ulice,
                    oznaka_ulice,
                    broj_stana,
                    telefon_fiksni,
                    telefon_mobilni,
                    slava_uid,
                    slavska_vodica,
                    uskrsnja_vodica,
                    napomena,
                ) = row
                parsed_data.append(
                    (
                        int(parohijan_uid) if parohijan_uid else 0,
                        ime_prezime or "",
                        int(ulica_uid) if ulica_uid else 0,
                        int(broj_ulice) if broj_ulice else 0,
                        oznaka_ulice or "",
                        int(broj_stana) if broj_stana else 0,
                        telefon_fiksni or "",
                        telefon_mobilni or "",
                        int(slava_uid) if slava_uid else 0,
                        slavska_vodica or "",
                        uskrsnja_vodica or "",
                        napomena or "",
                    )
                )

        return parsed_data
