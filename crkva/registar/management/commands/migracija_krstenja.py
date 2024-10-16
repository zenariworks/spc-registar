"""
Migracija tabele `HSPKRST.sqlite` (tabele krstenja) u tabelu 'krstenja'
"""
import sqlite3
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Hram, Svestenik, Krstenje, Parohija, Ulica, Parohijan, Adresa
from registar.management.commands.convert_utils import ConvertUtils
from datetime import date, time

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
    help = "Migracija tabele `HSPKRST.sqlite` (tabele krstenja) u tabelu 'krstenja'"

    def handle(self, *args, **kwargs):

        parsed_data = self._parse_data()
        #print(f"parsed_data: {len(parsed_data)}")

        created_count = 0

        for redni_broj_krstenja_tekuca_godina, \
                knjiga_krstenja, broj_krstenja, strana_krstenja, \
                adresa_deteta_grad, adresa_deteta_ulica, adresa_deteta_broj, godina_rodjenja_deteta, mesec_rodjenja_deteta, dan_rodjenja_deteta, vreme_rodjenja_deteta, mesto_rodjenja_deteta, \
                krstenje_godina, krstenje_mesec, krstenje_dan, krstenje_vreme, krstenje_mesto, hram, \
                ime_deteta, gradjansko_ime_deteta, pol_deteta, \
                ime_oca, prezime_oca, zanimanje_oca, adresa_oca_mesto, veroispovest_oca, narodnost_oca, \
                ime_majke, prezime_majke, zanimanje_majke, adresa_majke_mesto, veroispovest_majke, \
                dete_rodjeno_zivo, dete_po_redu_po_majci, dete_vanbracno, dete_blizanac, drugo_dete_blizanac_ime, dete_sa_telesnom_manom, \
                svestenik_id, ime_prezime_svestenika, zvanje_svestenika, parohija_id, \
                ime_kuma, prezime_kuma, zanimanje_kuma, adresa_kuma_mesto, \
                mesto_registracije, datum_registracije, maticni_broj, strana_registracije  in parsed_data:
            try:
                datum_krstenja = date(krstenje_godina, krstenje_mesec, krstenje_dan)
                vreme_krstenja = self._process_time_values(krstenje_vreme)

                datum_rodjenja_deteta = date(godina_rodjenja_deteta, mesec_rodjenja_deteta, dan_rodjenja_deteta) 
                vreme_rodjenja_deteta = self._process_time_values(vreme_rodjenja_deteta)

                # # tabela 'hramovi'
                hram_instance, _ = Hram.objects.get_or_create(naziv=ConvertUtils.latin_to_cyrillic(hram))
                svestenik_instance, _ =  Svestenik.objects.get_or_create(uid=svestenik_id)

                # krstenje = Krstenje(
                #     redni_broj_krstenja_tekuca_godina = redni_broj_krstenja_tekuca_godina,
                #     krstenje_tekuca_godina = krstenje_godina,
                #     # podaci za registar(protokol) krstenih
                #     knjiga_krstenja = knjiga_krstenja,
                #     broj_krstenja = broj_krstenja,
                #     strana_krstenja = strana_krstenja,
                #     # podaci o detetu
                #     adresa_deteta_grad = adresa_deteta_grad,
                #     adresa_deteta_ulica = adresa_deteta_ulica,
                #     adresa_deteta_broj = adresa_deteta_broj,
                #     datum_rodenja_deteta = datum_rodjenja_deteta,
                #     vreme_rodjenja_deteta = vreme_rodjenja_deteta,
                #     mesto_rodjenja = mesto_rodjenja_deteta,
                #     ime_deteta = ime_deteta,
                #     gradjansko_ime_deteta = gradjansko_ime_deteta,
                #     pol_deteta = pol_deteta,
                #     # podaci o krstenju
                #     datum_krstenja = datum_krstenja,
                #     vreme_krstenja = vreme_krstenja,
                #     mesto_krstenja = krstenje_mesto,
                #     hram = hram_instance,
                #     # podaci o roditeljima
                #     ime_oca = ime_oca,
                #     prezime_oca = prezime_oca,
                #     zanimanje_oca = zanimanje_oca,
                #     adresa_oca_mesto = adresa_oca_mesto,
                #     veroispovest_oca = veroispovest_oca,
                #     narodnost_oca = narodnost_oca,
                #     ime_majke = ime_majke,
                #     prezime_majke = prezime_majke,
                #     zanimanje_majke = zanimanje_majke,
                #     adresa_majke_mesto = adresa_majke_mesto,
                #     veroispovest_majke = veroispovest_majke,
                #     # ostali podaci o detetu
                #     dete_rodjeno_zivo = dete_rodjeno_zivo,
                #     dete_po_redu_po_majci = dete_po_redu_po_majci,
                #     dete_vanbracno = dete_vanbracno,
                #     dete_blizanac = dete_blizanac,
                #     drugo_dete_blizanac_ime = drugo_dete_blizanac_ime,
                #     dete_sa_telesnom_manom = dete_sa_telesnom_manom,
                #     # podaci o svesteniku
                #     svestenik = svestenik_instance,
                #     # podaci o kumu
                #     ime_kuma = ime_kuma,
                #     prezime_kuma = prezime_kuma,
                #     zanimanje_kuma = zanimanje_kuma,
                #     adresa_kuma_mesto = adresa_kuma_mesto,
                #     # podaci iz matične knjige
                #     mesto_registracije = mesto_registracije,
                #     datum_registracije = datum_registracije,
                #     maticni_broj = maticni_broj,
                #     strana_registracije = strana_registracije
                    
                #     # ime=ConvertUtils.latin_to_cyrillic(ime_prezime[0]),
                #     # prezime=ConvertUtils.latin_to_cyrillic(ime_prezime[1]),
                #     # mesto_rodjenja="",
                #     # datum_rodjenja=None,
                #     # vreme_rodjenja=None,
                #     # pol="",
                #     # devojacko_prezime="",
                #     # zanimanje="",
                #     # veroispovest="",
                #     # narodnost="",
                #     # adresa=adresa_instance,
                # )
                # krstenje.save()
                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'ulice': {created_count} нових уноса."
            )
        )

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
            #print("time_value_str: ", time_value_str)

            # Check if it contains a period `.`
            if '.' in time_value_str:
                HH = time_value_str.split(".")[0]
                MM = time_value_str.split(".")[1]
                HH = ConvertUtils.safe_convert_to_int(HH, 12)
                MM = ConvertUtils.safe_convert_to_int(MM, 0)
            # Check if it contains a comma `,`
            elif ',' in time_value_str:
                HH = time_value_str.split(",")[0]
                MM = time_value_str.split(",")[1]
                HH = ConvertUtils.safe_convert_to_int(HH, 12)
                MM = ConvertUtils.safe_convert_to_int(MM, 0)
            else:
                HH = time_value_str
                HH = ConvertUtils.safe_convert_to_int(HH, 12)
                MM = 0  # Set MM to 0 if no minutes are provided
            
            
            # Validate HH and MM
            if 0 <= HH < 24 and 0 <= MM <= 60:
                time_obj = time(HH, MM, 0)
            elif not (0 <= HH < 24):
                print("Invalid time: HH must be in [0, 24), HH: ", HH)
                if HH == 24:
                    HH = 0
                else:
                    HH = 12 # Default HH to 12 if invalid
                time_obj = time(HH, MM, 0)
            elif not (0 <= MM < 60): 
                print("Invalid time: MM must be in [0, 60), MM: ", MM)
                MM = 0  # Default MM to 0 if invalid
                time_obj = time(HH, MM, 0)

        return time_obj

    def _parse_data(self):
        """
        Migracija tabele 'HSPKRST.sqlite' 
            k_sifra         - redni_broj_krstenja_tekuca_godina
            k_aktgod        - godina krstenja
            k_datum         - datum krstenja
            
            // registar(protokol) krstenih
            k_proknj        - knjiga krstenja
            k_probr         - broj krstenja
            k_protst        - strana krstenja

            // podaci o detetu (adresa, mesto rodjenja)
            k_iz            - adresa deteta - grad
            k_ulica         - adresa detata - ulica
            k_broj          - adresa deteta - broj
            k_rodjgod       - godina rodjenja
            k_rodmese       - mesec rodjenja
            k_rodjdan       - dan rodjenja
            k_rodjvre       - vreme rodjenja
            k_rodjmest      - mesto rodjenja

            // podaci o krstenju
            k_krsgode       - godina krstenja
            k_krsmese       - mesec krstenja
            k_krsdan        - dan krstenja
            k_krsvre        - vreme krstenja
            k_krsmest       - mesto krstenja
            k_krshram       - hram krstenja

            // podaci o detetu
            k_detime        - ime deteta
            k_detimeg       - gradjansko ime deteta
            k_detpol        - pol deteta

            // podaci o roditeljima
            // otac
            k_rodime        - ime oca
            k_rodprez       - prezime oca
            k_rodzanim      - zanimanje oca
            k_rodmest       - adresa oca - mesto
            k_rodvera       - veroispovest roditelja - tu pise 'Pravoslavni, Srbi', to popunjava polje 'Veroispovest'
            k_rodnarod      - narodnost roditelja - ovo polje je prazno

            // majka
            k_rod2ime       - ime majke
            k_rod2prez      - prezime majke
            k_rod2zan       - zanimanje majke
            k_rod2mest      - adresa majke - mesto
            k_rod2vera      - veroispovest majke - tu pise 'Pravoslavni, Srbi', to popunjava polje 'Veroispovest'

            // ostali podaci o detetu
            k_detzivo       - da li je dete rodjeno zivo - stoji '1'
            k_detkoje       - koje je dete po redu (po majci)
            k_detbrac       - da li je dete vanbracno
            k_detbliz       - da li je dete blizanac
            k_detbliz2      - ako je blizanac, ko je drugo dete
            k_detmana       - da li dete sa telesnom manom

            // podaci o svesteniku
            k_rbrsve        - svestenik_id
            k_sveime        - ime i prezime svestenika
            k_svezvan       - zvanje svestenika
            k_svepar        - parohija_id svestenika (tu stoje i rimski brojevi, treba ih konvertovati u arapske)

            // podaci o kumovima
            k_kumime       - ime kuma
            k_kumprez      - prezime kuma
            k_kumzanim     - zanimanje kuma
            k_kummest      - adresa kuma - mesto

            // maticna knjiga
            k_regmesto     - mesto registracije (vrv opstinskog vencanja)
            k_regkada      - datum registracije
            k_regbroj      - maticni broj
            k_regstr       - strana registracije

        :return: Листа парсираних података ( ... )
        """
        parsed_data = []
        with sqlite3.connect("fixtures/combined_original_hsp_database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    k_sifra, 
                    k_proknj, k_protbr, k_protst, 
                    k_iz, k_ulica, k_broj, k_rodjgod, k_rodjmese, k_rodjdan, k_rodjvre, k_rodjmest, 
                    k_krsgod, k_krsmese, k_krsdan, k_krsvre, k_krsmest, k_krshram, 
                    k_detime, k_detimeg, k_detpol, 
                    k_rodime, k_rodprez, k_rodzanim, k_rodmest, k_rodvera, k_rodnarod, 
                    k_rod2ime, k_rod2prez, k_rod2zan, k_rod2mest, k_rod2vera, 
                    k_detzivo, k_detkoje, k_detbrac, k_detbliz, k_detbliz2, k_detmana, 
                    k_rbrsve, k_sveime, k_svezva, k_svepar, 
                    k_kumime, k_kumprez, k_kumzanim, k_kummest, 
                    k_regmesto, k_regkada, k_regbroj, k_regstr 
                FROM HSPKRST
            """)
            rows = cursor.fetchall()
            #print(f"Number of rows fetched: {len(rows)}")

            for row in rows: 
                redni_broj_krstenja_tekuca_godina, \
                knjiga_krstenja, broj_krstenja, strana_krstenja, \
                adresa_deteta_grad, adresa_deteta_ulica, adresa_deteta_broj, godina_rodjenja_deteta, mesec_rodjenja_deteta, dan_rodjenja_deteta, vreme_rodjenja_deteta, mesto_rodjenja_deteta, \
                krstenje_godina, krstenje_mesec, krstenje_dan, krstenje_vreme, krstenje_mesto, hram, \
                ime_deteta, gradjansko_ime_deteta, pol_deteta, \
                ime_oca, prezime_oca, zanimanje_oca, adresa_oca_mesto, veroispovest_oca, narodnost_oca, \
                ime_majke, prezime_majke, zanimanje_majke, adresa_majke_mesto, veroispovest_majke, \
                dete_rodjeno_zivo, dete_po_redu_po_majci, dete_vanbracno, dete_blizanac, drugo_dete_blizanac_ime, dete_sa_telesnom_manom, \
                svestenik_id, ime_prezime_svestenika, zvanje_svestenika, parohija_id, \
                ime_kuma, prezime_kuma, zanimanje_kuma, adresa_kuma_mesto, \
                mesto_registracije, datum_registracije, maticni_broj, strana_registracije = row
            
                parsed_data.append((redni_broj_krstenja_tekuca_godina, 
                    knjiga_krstenja, broj_krstenja, strana_krstenja, 
                    adresa_deteta_grad, adresa_deteta_ulica, adresa_deteta_broj, godina_rodjenja_deteta, mesec_rodjenja_deteta, dan_rodjenja_deteta, vreme_rodjenja_deteta, mesto_rodjenja_deteta, 
                    krstenje_godina, krstenje_mesec, krstenje_dan, krstenje_vreme, krstenje_mesto, hram, 
                    ime_deteta, gradjansko_ime_deteta, pol_deteta, 
                    ime_oca, prezime_oca, zanimanje_oca, adresa_oca_mesto, veroispovest_oca, narodnost_oca, 
                    ime_majke, prezime_majke, zanimanje_majke, adresa_majke_mesto, veroispovest_majke, 
                    dete_rodjeno_zivo, dete_po_redu_po_majci, dete_vanbracno, dete_blizanac, drugo_dete_blizanac_ime, dete_sa_telesnom_manom, 
                    svestenik_id, ime_prezime_svestenika, zvanje_svestenika, parohija_id, 
                    ime_kuma, prezime_kuma, zanimanje_kuma, adresa_kuma_mesto, 
                    mesto_registracije, datum_registracije, maticni_broj, strana_registracije ))
            
        return parsed_data

