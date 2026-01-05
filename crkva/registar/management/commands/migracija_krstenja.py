"""
Migracija tabele krstenja iz PostgreSQL staging tabele 'hsp_krstenja' u tabelu 'krstenja'
"""

import re
from datetime import date, time

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.convert_utils import Konvertor
from registar.models import Hram, Krstenje, Svestenik


class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'krstenja'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_krstenja"

    k_proknj --> Krstenje.knjiga
    k_protst --> Krstenje.strana

    k_iz + k_ulica

    k_rodjgod + k_rodmese + k_rodjdan --> Krstenje.dete <= Parohijan.datum_rodjenja
    k_rodjvre --> Krstenje.dete <= Parohijan.vreme_rodjenja
    k_rodjmesto --> Krstenje.dete <= Parohijan.mesto_rodjena
    k_rodjopst -->
    """

    help = "Migracija tabele krstenja iz PostgreSQL staging tabele 'hsp_krstenja'"

    def handle(self, *args, **kwargs):
        # clear the table before migrating the data
        Krstenje.objects.all().delete()

        parsed_data = self._parse_data()
        # print(f"parsed_data: {len(parsed_data)}")

        created_count = 0

        for (
            redni_broj_krstenja_tekuca_godina,
            knjiga,
            broj,
            strana,
            adresa_deteta_grad,
            adresa_deteta_ulica,
            adresa_deteta_broj,
            godina_rodjenja,
            mesec_rodjenja,
            dan_rodjenja,
            vreme_rodjenja,
            mesto_rodjenja,
            godina,
            mesec,
            dan,
            vreme,
            mesto,
            hram,
            ime_deteta,
            gradjansko_ime_deteta,
            pol_deteta,
            ime_oca,
            prezime_oca,
            zanimanje_oca,
            adresa_oca_mesto,
            veroispovest_oca,
            narodnost_oca,
            ime_majke,
            prezime_majke,
            zanimanje_majke,
            adresa_majke_mesto,
            veroispovest_majke,
            dete_rodjeno_zivo,
            dete_po_redu_po_majci,
            dete_vanbracno,
            dete_blizanac,
            drugo_dete_blizanac_ime,
            dete_sa_telesnom_manom,
            svestenik_id,
            ime_kuma,
            prezime_kuma,
            zanimanje_kuma,
            adresa_kuma_mesto,
            mesto_registracije,
            datum_registracije,
            maticni_broj,
            strana_registracije,
        ) in parsed_data:
            try:
                datum = date(godina, mesec, dan)
                vreme = self._process_time_values(vreme)

                datum_rodjenja = date(godina_rodjenja, mesec_rodjenja, dan_rodjenja)
                vreme_rodjenja = self._process_time_values(vreme_rodjenja)

                # # tabela 'hramovi'
                hram_samo_naziv = re.sub(r"(?i)\bhram\b", "", hram).strip()
                hram_instance, _ = Hram.objects.get_or_create(
                    naziv=Konvertor.string(hram_samo_naziv)
                )
                svestenik_instance, _ = Svestenik.objects.get_or_create(
                    uid=svestenik_id
                )

                # ako je gradjansko ime deteta definisano, npr. 'Хана' upisi '(грађанско Хана)
                if gradjansko_ime_deteta:
                    gradjansko_ime_deteta_ = (
                        f" (грађанско {Konvertor.string(gradjansko_ime_deteta)})"
                    )
                else:
                    gradjansko_ime_deteta_ = ""

                krstenje = Krstenje(
                    redni_broj_krstenja_tekuca_godina=redni_broj_krstenja_tekuca_godina,
                    krstenje_tekuca_godina=godina,
                    # podaci za registar(protokol) krstenih
                    knjiga=Konvertor.int(knjiga.rstrip(), 0),
                    broj=Konvertor.int(broj.rstrip(), 0),
                    strana=Konvertor.int(strana, 0),
                    # podaci o krstenju
                    datum=datum,
                    vreme=vreme,
                    mesto=Konvertor.string(mesto),
                    hram=hram_instance,
                    # podaci o detetu
                    adresa_deteta_grad=Konvertor.string(adresa_deteta_grad),
                    adresa_deteta_ulica=Konvertor.string(adresa_deteta_ulica),
                    adresa_deteta_broj=Konvertor.string(adresa_deteta_broj),
                    datum_rodjenja=datum_rodjenja,
                    vreme_rodjenja=vreme_rodjenja,
                    mesto_rodjenja=Konvertor.string(mesto_rodjenja),
                    ime_deteta=Konvertor.string(ime_deteta),
                    gradjansko_ime_deteta=gradjansko_ime_deteta_,
                    pol_deteta="М" if pol_deteta.rstrip() == "1" else "Ж",
                    # podaci o roditeljima
                    ime_oca=Konvertor.string(ime_oca),
                    prezime_oca=Konvertor.string(prezime_oca),
                    zanimanje_oca=Konvertor.string(zanimanje_oca),
                    adresa_oca_mesto=Konvertor.string(adresa_oca_mesto),
                    veroispovest_oca=Konvertor.string(veroispovest_oca),
                    narodnost_oca=Konvertor.string(narodnost_oca),
                    ime_majke=Konvertor.string(ime_majke),
                    prezime_majke=Konvertor.string(prezime_majke),
                    zanimanje_majke=Konvertor.string(zanimanje_majke),
                    adresa_majke_mesto=Konvertor.string(adresa_majke_mesto),
                    veroispovest_majke=Konvertor.string(veroispovest_majke),
                    # ostali podaci o detetu
                    dete_rodjeno_zivo=(
                        True if dete_rodjeno_zivo.rstrip() == "1" else False
                    ),
                    dete_po_redu_po_majci=self._get_child_str(dete_po_redu_po_majci),
                    dete_vanbracno=True if dete_vanbracno.rstrip() == "1" else False,
                    dete_blizanac=True if dete_blizanac.rstrip() == "1" else False,
                    drugo_dete_blizanac_ime=Konvertor.string(drugo_dete_blizanac_ime),
                    dete_sa_telesnom_manom=(
                        True if dete_sa_telesnom_manom.rstrip() == "1" else False
                    ),
                    # podaci o svesteniku
                    svestenik=svestenik_instance,
                    # podaci o kumu
                    ime_kuma=Konvertor.string(ime_kuma),
                    prezime_kuma=Konvertor.string(prezime_kuma),
                    zanimanje_kuma=Konvertor.string(zanimanje_kuma),
                    adresa_kuma_mesto=Konvertor.string(adresa_kuma_mesto),
                    # podaci iz matične knjige
                    mesto_registracije=Konvertor.string(mesto_registracije),
                    datum_registracije=datum_registracije
                    if datum_registracije
                    else None,
                    maticni_broj=maticni_broj if maticni_broj else None,
                    strana_registracije=strana_registracije
                    if strana_registracije
                    else None,
                    primedba="",
                )
                krstenje.save()
                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'крштења': {created_count} нових уноса."
            )
        )

        # Drop staging table after successful migration
        self._drop_staging_table()

    def _drop_staging_table(self):
        """Брише staging табелу 'hsp_krstenja' након успешне миграције."""
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hsp_krstenja")
        self.stdout.write(self.style.SUCCESS("Обрисана staging табела 'hsp_krstenja'."))

    def _get_child_str(self, child_num):
        """
        process `child_num` string to return a str object.

        Args:
            child_num (int): 1, 2, 3, 4, 5, 6, 7, 8, 9, 10

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

        # Check if child_num is within the valid range
        if 1 <= child_num <= 10:
            return ordinal_numbers[child_num - 1]  # Indexing starts from 0
        else:
            raise ValueError("child_num must be an integer between 1 and 10.")

    def _process_time_values(self, time_value_str):
        """
        process `time_value_str` string to return a time object.

        Args:
            time_value (str): The time in either 'HH.MM' or 'HH' format.

        Returns:
            time: A time object representing the processed time in format HH:MM:SS, or None if invalid.
        """
        # Initialize time_obj as None
        time_obj = None

        # Strip whitespace and check if the string is not empty
        if time_value_str.rstrip() not in ["", " ", None]:
            time_value_str = time_value_str.rstrip()
            # print("time_value_str: ", time_value_str)

            # Check if it contains a period `.`
            if "." in time_value_str:
                HH = time_value_str.split(".")[0]
                MM = time_value_str.split(".")[1]
                HH = Konvertor.int(HH, 12)
                MM = Konvertor.int(MM, 0)
            # Check if it contains a comma `,`
            elif "," in time_value_str:
                HH = time_value_str.split(",")[0]
                MM = time_value_str.split(",")[1]
                HH = Konvertor.int(HH, 12)
                MM = Konvertor.int(MM, 0)
            else:
                HH = time_value_str
                HH = Konvertor.int(HH, 12)
                MM = 0  # Set MM to 0 if no minutes are provided

            # Validate HH and MM
            if 0 <= HH < 24 and 0 <= MM <= 60:
                time_obj = time(HH, MM, 0)
            elif not (0 <= HH < 24):
                print("Invalid time: HH must be in [0, 24), HH: ", HH)
                if HH == 24:
                    HH = 0
                else:
                    HH = 12  # Default HH to 12 if invalid
                time_obj = time(HH, MM, 0)
            elif not (0 <= MM < 60):
                print("Invalid time: MM must be in [0, 60), MM: ", MM)
                MM = 0  # Default MM to 0 if invalid
                time_obj = time(HH, MM, 0)

        return time_obj

    def _parse_data(self):
        """
        Čita podatke iz PostgreSQL staging tabele 'hsp_krstenja'.
        :return: Lista parsiranih podataka
        """
        parsed_data = []
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    "K_SIFRA",
                    "K_PROKNJ", "K_PROTBR", "K_PROTST",
                    "K_IZ", "K_ULICA", "K_BROJ", "K_RODJGOD", "K_RODJMESE", "K_RODJDAN", "K_RODJVRE", "K_RODJMEST",
                    "K_KRSGOD", "K_KRSMESE", "K_KRSDAN", "K_KRSVRE", "K_KRSMEST", "K_KRSHRAM",
                    "K_DETIME", "K_DETIMEG", "K_DETPOL",
                    "K_RODIME", "K_RODPREZ", "K_RODZANIM", "K_RODMEST", "K_RODVERA", "K_RODNAROD",
                    "K_ROD2IME", "K_ROD2PREZ", "K_ROD2ZAN", "K_ROD2MEST", "K_ROD2VERA",
                    "K_DETZIVO", "K_DETKOJE", "K_DETBRAC", "K_DETBLIZ", "K_DETBLIZ2", "K_DETMANA",
                    "K_RBRSVE",
                    "K_KUMIME", "K_KUMPREZ", "K_KUMZANIM", "K_KUMMEST",
                    "K_REGMESTO", "K_REGKADA", "K_REGBROJ", "K_REGSTR"
                FROM hsp_krstenja
            """
            )
            krstenja = cursor.fetchall()

            for krstenje in krstenja:
                (
                    redni_broj_krstenja_tekuca_godina,
                    knjiga,
                    broj,
                    strana,
                    adresa_deteta_grad,
                    adresa_deteta_ulica,
                    adresa_deteta_broj,
                    godina_rodjenja,
                    mesec_rodjenja,
                    dan_rodjenja,
                    vreme_rodjenja,
                    mesto_rodjenja,
                    godina_krstenja,
                    mesec_krstenja,
                    dan_krstenja,
                    vreme_krstenja,
                    mesto_krstenja,
                    hram,
                    ime_deteta,
                    gradjansko_ime_deteta,
                    pol_deteta,
                    ime_oca,
                    prezime_oca,
                    zanimanje_oca,
                    adresa_oca_mesto,
                    veroispovest_oca,
                    narodnost_oca,
                    ime_majke,
                    prezime_majke,
                    zanimanje_majke,
                    adresa_majke_mesto,
                    veroispovest_majke,
                    dete_rodjeno_zivo,
                    dete_po_redu_po_majci,
                    dete_vanbracno,
                    dete_blizanac,
                    drugo_dete_blizanac_ime,
                    dete_sa_telesnom_manom,
                    svestenik_id,
                    ime_kuma,
                    prezime_kuma,
                    zanimanje_kuma,
                    adresa_kuma_mesto,
                    mesto_registracije,
                    datum_registracije,
                    maticni_broj,
                    strana_registracije,
                ) = krstenje

                # Convert string values to appropriate types
                parsed_data.append(
                    (
                        int(redni_broj_krstenja_tekuca_godina)
                        if redni_broj_krstenja_tekuca_godina
                        else 0,
                        knjiga or "",
                        broj or "",
                        int(strana) if strana else 0,
                        adresa_deteta_grad or "",
                        adresa_deteta_ulica or "",
                        adresa_deteta_broj or "",
                        int(godina_rodjenja) if godina_rodjenja else 1900,
                        int(mesec_rodjenja) if mesec_rodjenja else 1,
                        int(dan_rodjenja) if dan_rodjenja else 1,
                        vreme_rodjenja or "",
                        mesto_rodjenja or "",
                        int(godina_krstenja) if godina_krstenja else 1900,
                        int(mesec_krstenja) if mesec_krstenja else 1,
                        int(dan_krstenja) if dan_krstenja else 1,
                        vreme_krstenja or "",
                        mesto_krstenja or "",
                        hram or "",
                        ime_deteta or "",
                        gradjansko_ime_deteta or "",
                        pol_deteta or "",
                        ime_oca or "",
                        prezime_oca or "",
                        zanimanje_oca or "",
                        adresa_oca_mesto or "",
                        veroispovest_oca or "",
                        narodnost_oca or "",
                        ime_majke or "",
                        prezime_majke or "",
                        zanimanje_majke or "",
                        adresa_majke_mesto or "",
                        veroispovest_majke or "",
                        dete_rodjeno_zivo or "",
                        int(dete_po_redu_po_majci) if dete_po_redu_po_majci else 1,
                        dete_vanbracno or "",
                        dete_blizanac or "",
                        drugo_dete_blizanac_ime or "",
                        dete_sa_telesnom_manom or "",
                        int(svestenik_id) if svestenik_id else 0,
                        ime_kuma or "",
                        prezime_kuma or "",
                        zanimanje_kuma or "",
                        adresa_kuma_mesto or "",
                        mesto_registracije or "",
                        datum_registracije or "",
                        maticni_broj or "",
                        strana_registracije or "",
                    )
                )

        return parsed_data
