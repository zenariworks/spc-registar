"""
Migracija tabele `HSPVENC.sqlite` (tabele vencanja) u tabelu 'vencanja'
"""
import sqlite3
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Hram, Svestenik, Vencanje
from registar.management.commands.convert_utils import ConvertUtils
from datetime import date, time

class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'vencanja'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_vencanja"
    """
    help = "Migracija tabele `HSPVENC.sqlite` (tabele vencanja) u tabelu 'vencanja'"

    def handle(self, *args, **kwargs):

        parsed_data = self._parse_data()
        #print(f"parsed_data: {len(parsed_data)}")

        created_count = 0

        for redni_broj_vencanja_tekuca_godina, vencanje_tekuca_godina, \
            knjiga, strana, broj, \
            datum, \
            ime_zenika, prezime_zenika, zanimanje_zenika, mesto_zenika, veroispovest_zenika, narodnost_zenika, adresa_zenika, \
            ime_neveste, prezime_neveste, zanimanje_neveste, mesto_neveste, veroispovest_neveste, narodnost_neveste, adresa_neveste, \
            ime_oca_zenika, ime_majke_zenika, ime_oca_neveste, ime_majke_neveste, \
            godina_rodjenja_zenika, mesec_rodjenja_zenika, dan_rodjenja_zenika, mesto_rodjenja_zenika, godina_rodjenja_neveste, mesec_rodjenja_neveste, dan_rodjenja_neveste, mesto_rodjenja_neveste, \
            brak_po_redu_zenika, brak_po_redu_neveste, \
            godina_ispitivanja, mesec_ispitivanja, dan_ispitivanja, naziv_hrama, svestenik_id, \
            ime_kuma, ime_svedoka, \
            razresenje, razresenje_primedba in parsed_data:
            try:
                hram_instance, _ = Hram.objects.get_or_create(naziv=ConvertUtils.latin_to_cyrillic(naziv_hrama))
                svestenik_instance, _ =  Svestenik.objects.get_or_create(uid=svestenik_id)

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
                    redni_broj_vencanja_tekuca_godina = redni_broj_vencanja_tekuca_godina,
                    vencanje_tekuca_godina = vencanje_tekuca_godina,
                    knjiga = ConvertUtils.safe_convert_to_int(knjiga, 0),
                    strana = ConvertUtils.safe_convert_to_int(strana, 0),
                    tekuci_broj = ConvertUtils.safe_convert_to_int(broj, 0),
                    datum = datum,
                    ime_zenika = ConvertUtils.latin_to_cyrillic(ime_zenika),
                    prezime_zenika = ConvertUtils.latin_to_cyrillic(prezime_zenika),
                    zanimanje_zenika = ConvertUtils.latin_to_cyrillic(zanimanje_zenika),
                    mesto_zenika = ConvertUtils.latin_to_cyrillic(mesto_zenika),
                    veroispovest_zenika = ConvertUtils.latin_to_cyrillic(veroispovest_zenika),
                    narodnost_zenika = ConvertUtils.latin_to_cyrillic(narodnost_zenika),
                    adresa_zenika = ConvertUtils.latin_to_cyrillic(adresa_zenika),
                    ime_neveste = ConvertUtils.latin_to_cyrillic(ime_neveste),
                    prezime_neveste = ConvertUtils.latin_to_cyrillic(prezime_neveste),
                    zanimanje_neveste = ConvertUtils.latin_to_cyrillic(zanimanje_neveste),
                    mesto_neveste = ConvertUtils.latin_to_cyrillic(mesto_neveste),
                    veroispovest_neveste = ConvertUtils.latin_to_cyrillic(veroispovest_neveste),
                    narodnost_neveste = ConvertUtils.latin_to_cyrillic(narodnost_neveste),
                    adresa_neveste = ConvertUtils.latin_to_cyrillic(adresa_neveste),
                    svekar = ConvertUtils.latin_to_cyrillic(ime_oca_zenika),
                    svekrva = ConvertUtils.latin_to_cyrillic(ime_majke_zenika),
                    tast = ConvertUtils.latin_to_cyrillic(ime_oca_neveste),
                    tasta = ConvertUtils.latin_to_cyrillic(ime_majke_neveste),
                    datum_rodjenja_zenika = date(godina_rodjenja_zenika, mesec_rodjenja_zenika, dan_rodjenja_zenika),
                    mesto_rodjenja_zenika = ConvertUtils.latin_to_cyrillic(mesto_rodjenja_zenika),
                    datum_rodjenja_neveste = date(godina_rodjenja_neveste, mesec_rodjenja_neveste, dan_rodjenja_neveste),
                    mesto_rodjenja_neveste = ConvertUtils.latin_to_cyrillic(mesto_rodjenja_neveste),
                    zenik_rb_brak = "први" if brak_po_redu_zenika  == 1 else "други",
                    nevesta_rb_brak = "први" if brak_po_redu_neveste  == 1 else "други",
                    datum_ispita = date(godina_ispitivanja, mesec_ispitivanja, dan_ispitivanja),
                    hram = hram_instance,
                    svestenik = svestenik_instance,
                    kum = ConvertUtils.latin_to_cyrillic(ime_kuma),
                    stari_svat = ConvertUtils.latin_to_cyrillic(ime_svedoka), 
                    razresenje = "нису" if razresenje.rstrip()  == "N" else "јесу",
                    razresenje_primedba = ConvertUtils.latin_to_cyrillic(razresenje_primedba),
                    primedba = ""
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

    def _get_marriage_str(self, marriage_num):
        """
        process `marriage_num` string to return a str object.
        
        Args:
            marriage_num (int): 1, 2, 3 
            
        Returns:
            str: A str object: 'прво', 'друго', 'треће', 'четврто', 'пето', 'шесто', 'седмо', 'осмо', 'девето', 'десето'
        """

        # List of Serbian ordinal numbers
        ordinal_numbers = [
            'прво',   # 1
            'друго',  # 2
            'треће',  # 3
            'четврто',# 4
            'пето',   # 5
            'шесто',  # 6
            'седмо',  # 7
            'осмо',   # 8
            'девето',  # 9
            'десето'   # 10
        ]
        
        # Check if child_num is within the valid range
        if 1 <= child_num <= 10:
            return ordinal_numbers[child_num - 1]  # Indexing starts from 0
        else:
            raise ValueError("child_num must be an integer between 1 and 10.")

    
    def _parse_data(self):
        """
        Migracija tabele 'HSPVENC.sqlite' 
            v_sifra         - redni_broj_vencanja_tekuca_godina
            v_aktgod        - godina vencanja
            
            // registar(protokol) vencanih
            v_knjiga        - knjiga vencanja
            k_strana        - strana vencanja
            k_tekbroj       - broj vencanja
            
            // podaci o vencanima (zenik, tj. mladozenja)
            v_datum         - datum vencanja
            v_z_ime         - ime zenika
            v_z_prez        - prezime zenika
            v_z_zanim       - zanimanje zenika
            v_z_mesto       - mesto zenika
            v_z_verois      - veroispovest zenika
            v_z_narodn      - narodnost zenika
            v_z_adresa      - adresa zenika

            // podaci o vencanima (nevesta)
            v_n_ime         - ime neveste
            v_n_prez        - prezime neveste
            v_n_zanim       - zanimanje neveste
            v_n_mesto       - mesto neveste
            v_n_verois      - veroispopvest neveste
            v_n_narodn      - narodnost neveste
            v_n_adresa      - adresa neveste

            // podaci o roditeljima mladozenje i neveste
            v_zr_otac       - ime i zanimanje oca mladozenje
            v_zr_majka      - ime i zanimanje majke mladozenje
            v_nr_otac       - ime i zanimanje oca neveste
            v_nr_majka      - ime i zanimanje majke neveste

            // podaci o rodjenju mladozenje i neveste
            v_z_rodjg       - godina rodjenja mladozenje
            v_z_rodjm       - mesec rodjenja mladozenje
            v_z_rodjd       - dan rodjenja mladozenje
            v_z_rodjme      - mesto rodjenja mladozenje
            v_n_rodjg       - godina rodjenja neveste
            v_n_rodjm       - mesec rodjenja neveste
            v_n_rodjd       - dan rodjenja neveste
            v_n_rodjme      - mesto rodjenja neveste

            // podaci o prethodnim brakovima (ako ih je bilo)
            v_z_brak        - u koji brak po redu stupa mladozenja
            v_n_brak        - u koji brak po redu stupa nevesta

            // oglasenje (podaci o predbracnom ispitu i datumu vencanja) 
            v_ispitgod      - godina ispitivanja
            v_ispitmes      - mesec ispitivanja
            v_ispitdan      - dan ispitivanja
            v_godina        - godina vencanja
            v_mesec         - mesec vencanja
            v_dan           - dan vencanja
            v_hrmesto       - mesto hrama, tj. mesto vencanja
            v_hrime         - naziv hrama
            v_rbrsvesti     - svestenik_id

            // podaci svedocima (kum i stari svat)
            v_kumime        - ime kuma, zanimanje i mesto 
            v_ssvat         - ime starog svata, zanimanje i mesto

            // podaci o razresenju
            v_razrdn        - supruznici su imali potrebu razresenja (Da/Ne)
            v_razrtxt       - ako jesu, ko je dao razresenje

        :return: Листа парсираних података ( ... )
        """
        parsed_data = []
        with sqlite3.connect("fixtures/combined_original_hsp_database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    v_sifra, v_aktgod,
                    v_knjiga, v_strana, v_tekbroj,
                    v_datum, v_z_ime, v_z_prez, v_z_zanim, v_z_mesto, v_z_verois, v_z_narodn, v_z_adresa,
                    v_n_ime, v_n_prez, v_n_zanim, v_n_mesto, v_n_verois, v_n_narodn, v_n_adresa,
                    v_zr_otac, v_zr_majka, v_nr_otac, v_nr_majka,
                    v_z_rodjg, v_z_rodjm, v_z_rodjd, v_z_rodjme, v_n_rodjg, v_n_rodjm, v_n_rodjd, v_n_rodjme,
                    v_z_brak, v_n_brak,
                    v_ispitgod, v_ispitmes, v_ispitdan, v_hrime, v_rbrsvest,
                    v_kum, v_ssvat,
                    v_razrdn, v_razrtxt
                FROM HSPVENC
            """)
            vencanja = cursor.fetchall()
            #print(f"Number of rows fetched: {len(vencanja)}")

            for vencanje in vencanja: 
                redni_broj_vencanja_tekuca_godina, vencanje_tekuca_godina, \
                knjiga, strana, broj, \
                datum, \
                ime_zenika, prezime_zenika, zanimanje_zenika, mesto_zenika, veroispovest_zenika, narodnost_zenika, adresa_zenika, \
                ime_neveste, prezime_neveste, zanimanje_neveste, mesto_neveste, veroispovest_neveste, narodnost_neveste, adresa_neveste, \
                ime_oca_zenika, ime_majke_zenika, ime_oca_neveste, ime_majke_neveste, \
                godina_rodjenja_zenika, mesec_rodjenja_zenika, dan_rodjenja_zenika, mesto_rodjenja_zenika, godina_rodjenja_neveste, mesec_rodjenja_neveste, dan_rodjenja_neveste, mesto_rodjenja_neveste, \
                brak_po_redu_zenika, brak_po_redu_neveste, \
                godina_ispitivanja, mesec_ispitivanja, dan_ispitivanja, naziv_hrama, svestenik_id, \
                ime_kuma, ime_svedoka, \
                razresenje, razresenje_primedba = vencanje
            
                parsed_data.append((redni_broj_vencanja_tekuca_godina, vencanje_tekuca_godina,
                    knjiga, strana, broj,
                    datum,
                    ime_zenika, prezime_zenika, zanimanje_zenika, mesto_zenika, veroispovest_zenika, narodnost_zenika, adresa_zenika,
                    ime_neveste, prezime_neveste, zanimanje_neveste, mesto_neveste, veroispovest_neveste, narodnost_neveste, adresa_neveste,
                    ime_oca_zenika, ime_majke_zenika, ime_oca_neveste, ime_majke_neveste,
                    godina_rodjenja_zenika, mesec_rodjenja_zenika, dan_rodjenja_zenika, mesto_rodjenja_zenika, godina_rodjenja_neveste, mesec_rodjenja_neveste, dan_rodjenja_neveste, mesto_rodjenja_neveste,
                    brak_po_redu_zenika, brak_po_redu_neveste,
                    godina_ispitivanja, mesec_ispitivanja, dan_ispitivanja, naziv_hrama, svestenik_id,
                    ime_kuma, ime_svedoka,
                    razresenje, razresenje_primedba ))

        return parsed_data

