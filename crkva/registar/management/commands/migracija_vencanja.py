"""
Migracija tabele vencanja iz PostgreSQL staging tabele 'hsp_vencanja' u tabelu 'vencanja'
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.convert_utils import Konvertor
from registar.models import Hram, Svestenik, Vencanje


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'vencanja'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_vencanja"
    """

    help = "Migracija tabele vencanja iz PostgreSQL staging tabele 'hsp_vencanja'"

    def handle(self, *args, **kwargs):
        # clear the table before migrating the data
        Vencanje.objects.all().delete()

        parsed_data = self._parse_data()
        # print(f"parsed_data: {len(parsed_data)}")

        created_count = 0

        for (
            redni_broj_vencanja_tekuca_godina,
            vencanje_tekuca_godina,
            knjiga,
            strana,
            broj,
            datum,
            ime_zenika,
            prezime_zenika,
            zanimanje_zenika,
            mesto_zenika,
            veroispovest_zenika,
            narodnost_zenika,
            adresa_zenika,
            ime_neveste,
            prezime_neveste,
            zanimanje_neveste,
            mesto_neveste,
            veroispovest_neveste,
            narodnost_neveste,
            adresa_neveste,
            ime_oca_zenika,
            ime_majke_zenika,
            ime_oca_neveste,
            ime_majke_neveste,
            godina_rodjenja_zenika,
            mesec_rodjenja_zenika,
            dan_rodjenja_zenika,
            mesto_rodjenja_zenika,
            godina_rodjenja_neveste,
            mesec_rodjenja_neveste,
            dan_rodjenja_neveste,
            mesto_rodjenja_neveste,
            brak_po_redu_zenika,
            brak_po_redu_neveste,
            godina_ispitivanja,
            mesec_ispitivanja,
            dan_ispitivanja,
            naziv_hrama,
            svestenik_id,
            ime_kuma,
            ime_svedoka,
            razresenje,
            razresenje_primedba,
        ) in parsed_data:
            try:
                hram_naziv = Konvertor.string(naziv_hrama)
                hram_instance = Hram.objects.filter(naziv=hram_naziv).first()
                if not hram_instance:
                    hram_instance = Hram.objects.create(naziv=hram_naziv)
                svestenik_instance, _ = Svestenik.objects.get_or_create(
                    uid=svestenik_id
                )

                # postoji jedan record gde je za godinu rodjenja upisano 0
                # Taj record cu zakucati na 01.01.1900 godine
                if godina_rodjenja_zenika == 0:
                    godina_rodjenja_zenika = 1900
                if mesec_rodjenja_zenika == 0:
                    mesec_rodjenja_zenika = 1
                if dan_rodjenja_zenika == 0:
                    dan_rodjenja_zenika = 1

                if godina_rodjenja_neveste == 0:
                    godina_rodjenja_neveste = 1900
                if mesec_rodjenja_neveste == 0:
                    mesec_rodjenja_neveste = 1
                if dan_rodjenja_neveste == 0:
                    dan_rodjenja_neveste = 1

                if godina_ispitivanja == 0:
                    godina_ispitivanja = 1900
                if mesec_ispitivanja == 0:
                    mesec_ispitivanja = 1
                if dan_ispitivanja == 0:
                    dan_ispitivanja = 1

                vencanje = Vencanje(
                    redni_broj_vencanja_tekuca_godina=redni_broj_vencanja_tekuca_godina,
                    vencanje_tekuca_godina=vencanje_tekuca_godina,
                    knjiga=Konvertor.int(knjiga, 0),
                    strana=Konvertor.int(strana, 0),
                    tekuci_broj=Konvertor.int(broj, 0),
                    datum=datum if datum else None,
                    ime_zenika=Konvertor.string(ime_zenika),
                    prezime_zenika=Konvertor.string(prezime_zenika),
                    zanimanje_zenika=Konvertor.string(zanimanje_zenika),
                    mesto_zenika=Konvertor.string(mesto_zenika),
                    veroispovest_zenika=Konvertor.string(veroispovest_zenika),
                    narodnost_zenika=Konvertor.string(narodnost_zenika),
                    adresa_zenika=Konvertor.string(adresa_zenika),
                    ime_neveste=Konvertor.string(ime_neveste),
                    prezime_neveste=Konvertor.string(prezime_neveste),
                    zanimanje_neveste=Konvertor.string(zanimanje_neveste),
                    mesto_neveste=Konvertor.string(mesto_neveste),
                    veroispovest_neveste=Konvertor.string(veroispovest_neveste),
                    narodnost_neveste=Konvertor.string(narodnost_neveste),
                    adresa_neveste=Konvertor.string(adresa_neveste),
                    svekar=Konvertor.string(ime_oca_zenika),
                    svekrva=Konvertor.string(ime_majke_zenika),
                    tast=Konvertor.string(ime_oca_neveste),
                    tasta=Konvertor.string(ime_majke_neveste),
                    datum_rodjenja_zenika=date(
                        godina_rodjenja_zenika,
                        mesec_rodjenja_zenika,
                        dan_rodjenja_zenika,
                    ),
                    mesto_rodjenja_zenika=Konvertor.string(mesto_rodjenja_zenika),
                    datum_rodjenja_neveste=date(
                        godina_rodjenja_neveste,
                        mesec_rodjenja_neveste,
                        dan_rodjenja_neveste,
                    ),
                    mesto_rodjenja_neveste=Konvertor.string(mesto_rodjenja_neveste),
                    zenik_rb_brak="први" if brak_po_redu_zenika == 1 else "други",
                    nevesta_rb_brak="први" if brak_po_redu_neveste == 1 else "други",
                    datum_ispita=date(
                        godina_ispitivanja, mesec_ispitivanja, dan_ispitivanja
                    ),
                    hram=hram_instance,
                    svestenik=svestenik_instance,
                    kum=Konvertor.string(ime_kuma),
                    stari_svat=Konvertor.string(ime_svedoka),
                    razresenje="нису" if razresenje.rstrip() == "N" else "јесу",
                    razresenje_primedba=Konvertor.string(razresenje_primedba),
                    primedba="",
                )
                vencanje.save()
                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'венчања': {created_count} нових уноса."
            )
        )

    def _get_marriage_str(self, _marriage_num):
        """
        process `marriage_num` string to return a str object.

        Args:
            _marriage_num (int): 1, 2, 3 (currently unused)

        Returns:
            str: A str object: 'прво', 'друго', 'треће', 'четврто', 'пето', 'шесто', 'седмо', 'осмо', 'девето', 'десето'
        """

        # List of Serbian ordinal numbers
        ordinal_numbers = [
            "прво",  # 1
            "друго",  # 2
            "треће",  # 3
            "четврто",  # 4
            "пето",  # 5
            "шесто",  # 6
            "седмо",  # 7
            "осмо",  # 8
            "девето",  # 9
            "десето",  # 10
        ]

        # Check if marriage_num is within the valid range
        if 1 <= _marriage_num <= 10:
            return ordinal_numbers[_marriage_num - 1]  # Indexing starts from 0

        raise ValueError("marriage_num must be an integer between 1 and 10.")

    def _parse_data(self):
        """
        Čita podatke iz PostgreSQL staging tabele 'hsp_vencanja'.
        :return: Lista parsiranih podataka
        """
        parsed_data = []
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    "V_SIFRA", "V_AKTGOD",
                    "V_KNJIGA", "V_STRANA", "V_TEKBROJ",
                    "V_DATUM", "V_Z_IME", "V_Z_PREZ", "V_Z_ZANIM", "V_Z_MESTO", "V_Z_VEROIS", "V_Z_NARODN", "V_Z_ADRESA",
                    "V_N_IME", "V_N_PREZ", "V_N_ZANIM", "V_N_MESTO", "V_N_VEROIS", "V_N_NARODN", "V_N_ADRESA",
                    "V_ZR_OTAC", "V_ZR_MAJKA", "V_NR_OTAC", "V_NR_MAJKA",
                    "V_Z_RODJG", "V_Z_RODJM", "V_Z_RODJD", "V_Z_RODJME", "V_N_RODJG", "V_N_RODJM", "V_N_RODJD", "V_N_RODJME",
                    "V_Z_BRAK", "V_N_BRAK",
                    "V_ISPITGOD", "V_ISPITMES", "V_ISPITDAN", "V_HRIME", "V_RBRSVEST",
                    "V_KUM", "V_SSVAT",
                    "V_RAZRDN", "V_RAZRTXT"
                FROM hsp_vencanja
            """
            )
            vencanja = cursor.fetchall()

            for vencanje in vencanja:
                (
                    redni_broj_vencanja_tekuca_godina,
                    vencanje_tekuca_godina,
                    knjiga,
                    strana,
                    broj,
                    datum,
                    ime_zenika,
                    prezime_zenika,
                    zanimanje_zenika,
                    mesto_zenika,
                    veroispovest_zenika,
                    narodnost_zenika,
                    adresa_zenika,
                    ime_neveste,
                    prezime_neveste,
                    zanimanje_neveste,
                    mesto_neveste,
                    veroispovest_neveste,
                    narodnost_neveste,
                    adresa_neveste,
                    ime_oca_zenika,
                    ime_majke_zenika,
                    ime_oca_neveste,
                    ime_majke_neveste,
                    godina_rodjenja_zenika,
                    mesec_rodjenja_zenika,
                    dan_rodjenja_zenika,
                    mesto_rodjenja_zenika,
                    godina_rodjenja_neveste,
                    mesec_rodjenja_neveste,
                    dan_rodjenja_neveste,
                    mesto_rodjenja_neveste,
                    brak_po_redu_zenika,
                    brak_po_redu_neveste,
                    godina_ispitivanja,
                    mesec_ispitivanja,
                    dan_ispitivanja,
                    naziv_hrama,
                    svestenik_id,
                    ime_kuma,
                    ime_svedoka,
                    razresenje,
                    razresenje_primedba,
                ) = vencanje

                parsed_data.append(
                    (
                        int(redni_broj_vencanja_tekuca_godina)
                        if redni_broj_vencanja_tekuca_godina
                        else 0,
                        int(vencanje_tekuca_godina) if vencanje_tekuca_godina else 1900,
                        knjiga or "",
                        strana or "",
                        broj or "",
                        datum or "",
                        ime_zenika or "",
                        prezime_zenika or "",
                        zanimanje_zenika or "",
                        mesto_zenika or "",
                        veroispovest_zenika or "",
                        narodnost_zenika or "",
                        adresa_zenika or "",
                        ime_neveste or "",
                        prezime_neveste or "",
                        zanimanje_neveste or "",
                        mesto_neveste or "",
                        veroispovest_neveste or "",
                        narodnost_neveste or "",
                        adresa_neveste or "",
                        ime_oca_zenika or "",
                        ime_majke_zenika or "",
                        ime_oca_neveste or "",
                        ime_majke_neveste or "",
                        int(godina_rodjenja_zenika) if godina_rodjenja_zenika else 0,
                        int(mesec_rodjenja_zenika) if mesec_rodjenja_zenika else 0,
                        int(dan_rodjenja_zenika) if dan_rodjenja_zenika else 0,
                        mesto_rodjenja_zenika or "",
                        int(godina_rodjenja_neveste) if godina_rodjenja_neveste else 0,
                        int(mesec_rodjenja_neveste) if mesec_rodjenja_neveste else 0,
                        int(dan_rodjenja_neveste) if dan_rodjenja_neveste else 0,
                        mesto_rodjenja_neveste or "",
                        int(brak_po_redu_zenika) if brak_po_redu_zenika else 1,
                        int(brak_po_redu_neveste) if brak_po_redu_neveste else 1,
                        int(godina_ispitivanja) if godina_ispitivanja else 0,
                        int(mesec_ispitivanja) if mesec_ispitivanja else 0,
                        int(dan_ispitivanja) if dan_ispitivanja else 0,
                        naziv_hrama or "",
                        int(svestenik_id) if svestenik_id else 0,
                        ime_kuma or "",
                        ime_svedoka or "",
                        razresenje or "",
                        razresenje_primedba or "",
                    )
                )

        return parsed_data
