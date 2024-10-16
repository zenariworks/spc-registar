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

        # tabela 'hramovi': Cukarica, Srbija
        adresa_instance, _ = Adresa.objects.get_or_create(broj=35, sprat=None, broj_stana=None, dodatak=None, 
                                                          postkod=None, primedba=None, ulica=Ulica.objects.get(uid=21))
        hram_instance, _ = Hram.objects.get_or_create(naziv="Храм Свете Петке", adresa=adresa_instance)

        # Output the uids
        #print("opstina UID:", opstina_instance.uid)
        #print("mesto UID:", mesto_instance.uid)
        #print("drzava UID:", drzava_instance.uid)
       
        parsed_data = self._parse_data()
        created_count = 0

        for redni_broj_krstenja_tekuca_godina, godina_krstenja, datum_krstenja, \
                knjiga_krstenja, broj_krstenja, strana_krstenja, \
                adresa_deteta_grad, adresa_deteta_ulica, adresa_deteta_broj, \
                godina_rodjenja, mesec_rodjenja, dan_rodjenja, vreme_rodjenja, mesto_rodjenja, \
                godina_krstenja, mesec_krstenja, dan_krstenja, vreme_krstenja, mesto_krstenja, hram_krstenja, \
                ime_deteta, gradjansko_ime_deteta, pol_deteta, \
                ime_oca, prezime_oca, zanimanje_oca, adresa_oca_mesto, veroispovest_oca, narodnost_oca, \
                ime_majke, prezime_majke, zanimanje_majke, adresa_majke_mesto, veroispovest_majke, \
                dete_rodjeno_zivo, dete_po_redu_po_majci, dete_vanbracno, dete_blizanac, drugo_dete_blizanac, dete_sa_telesnom_manom, \
                svestenik_id, ime_prezime_svestenika, zvanje_svestenika, parohija_id, \
                ime_kuma, prezime_kuma, zanimanje_kuma, adresa_kuma_mesto, \
                mesto_registracije, datum_registracije, maticni_broj, strana_registracije in parsed_data:
            try:
                datum_krstenja = date(godina_krstenja.rstrip(), mesec_krstenja.rstrip(), dan_krstenja.rstrip())
                HH = (vreme_krstenja.rstrip()).split(".")[0]
                MM = (vreme_krstenja.rstrip()).split(".")[1]
                vreme_krstenja = time(HH, MM, 0) # Time in format HH:MM:SS

                svestenik_instance, _ =  Svestenik.objects.get_or_create(uid=svestenik_id)


                # # razdvoji ime i prezime" "ime prezime" -> ["ime", "prezime"]
                # # i unesi kao ime i prezime
                # ime_prezime = ime_prezime.split(" ")

                #krstenje = Krstenje(
                    # ime=ConvertUtils.latin_to_cyrillic(ime_prezime[0]),
                    # prezime=ConvertUtils.latin_to_cyrillic(ime_prezime[1]),
                    # mesto_rodjenja="",
                    # datum_rodjenja=None,
                    # vreme_rodjenja=None,
                    # pol="",
                    # devojacko_prezime="",
                    # zanimanje="",
                    # veroispovest="",
                    # narodnost="",
                    # adresa=adresa_instance,
                #)
                #krstenje.save()
                #created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'ulice': {created_count} нових уноса."
            )
        )

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
                    k_sifra, k_aktgod, k_datum, 
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

            for row in rows: redni_broj_krstenja_tekuca_godina, godina_krstenja, datum_krstenja, \
                knjiga_krstenja, broj_krstenja, strana_krstenja, \
                adresa_deteta_grad, adresa_deteta_ulica, adresa_deteta_broj, \
                godina_rodjenja, mesec_rodjenja, dan_rodjenja, vreme_rodjenja, mesto_rodjenja, \
                godina_krstenja, mesec_krstenja, dan_krstenja, vreme_krstenja, mesto_krstenja, hram_krstenja, \
                ime_deteta, gradjansko_ime_deteta, pol_deteta, \
                ime_oca, prezime_oca, zanimanje_oca, adresa_oca_mesto, veroispovest_oca, narodnost_oca, \
                ime_majke, prezime_majke, zanimanje_majke, adresa_majke_mesto, veroispovest_majke, \
                dete_rodjeno_zivo, dete_po_redu_po_majci, dete_vanbracno, dete_blizanac, drugo_dete_blizanac, dete_sa_telesnom_manom, \
                svestenik_id, ime_prezime_svestenika, zvanje_svestenika, parohija_id, \
                ime_kuma, prezime_kuma, zanimanje_kuma, adresa_kuma_mesto, \
                mesto_registracije, datum_registracije, maticni_broj, strana_registracije = row
            
            parsed_data.append((redni_broj_krstenja_tekuca_godina, godina_krstenja, datum_krstenja, \
                knjiga_krstenja, broj_krstenja, strana_krstenja, \
                adresa_deteta_grad, adresa_deteta_ulica, adresa_deteta_broj, \
                godina_rodjenja, mesec_rodjenja, dan_rodjenja, vreme_rodjenja, mesto_rodjenja, \
                godina_krstenja, mesec_krstenja, dan_krstenja, vreme_krstenja, mesto_krstenja, hram_krstenja, \
                ime_deteta, gradjansko_ime_deteta, pol_deteta, \
                ime_oca, prezime_oca, zanimanje_oca, adresa_oca_mesto, veroispovest_oca, narodnost_oca, \
                ime_majke, prezime_majke, zanimanje_majke, adresa_majke_mesto, veroispovest_majke, \
                dete_rodjeno_zivo, dete_po_redu_po_majci, dete_vanbracno, dete_blizanac, drugo_dete_blizanac, dete_sa_telesnom_manom, \
                svestenik_id, ime_prezime_svestenika, zvanje_svestenika, parohija_id, \
                ime_kuma, prezime_kuma, zanimanje_kuma, adresa_kuma_mesto, \
                mesto_registracije, datum_registracije, maticni_broj, strana_registracije))
            
            return parsed_data


#
# class Command(BaseCommand):

#     def create_random_krstenje(self, parohijan):
#         """Креира насумично крштење."""
#         dete = self.random_parohijan("М" if random.choice([True, False]) else "Ж")
#         otac = self.random_parohijan("М", min_age=20)
#         majka = self.random_parohijan("Ж", min_age=20)
#         kum = self.random_parohijan(
#             "М" if random.choice([True, False]) else "Ж", min_age=20
#         )
#         svestenik = self.create_random_svestenik()
#         hram = Hram.objects.order_by("?").first()

#         krstenje = Krstenje(
#             knjiga=random.randint(1, 100),
#             strana=random.randint(1, 500),
#             tekuci_broj=random.randint(1, 1000),
#             datum=RandomUtils.random_datetime().date(),
#             vreme=RandomUtils.random_datetime().time(),
#             hram=hram,
#             dete=dete,
#             dete_majci=random.randint(1, 10),
#             dete_bracno=random.choice([True, False]),
#             mana=random.choice([True, False]),
#             blizanac=self.random_parohijan(
#                 "М" if random.choice([True, False]) else "Ж"
#             ),
#             otac=otac,
#             majka=majka,
#             svestenik=svestenik,
#             kum=kum,
#             primedba="Примедба...",
#         )
#         krstenje.save()

#     def handle(self, *args, **kwargs):
#         parohijani = []
#         for _ in range(10):
#             parohijani.append(RandomUtils.create_random_parohijan(unesi_adresu, "М"))
#             parohijani.append(RandomUtils.create_random_parohijan(unesi_adresu, "Ж"))

#         for _ in range(5):
#             RandomUtils.create_random_hram(unesi_adresu)

#         for _ in range(2):
#             self.create_random_svestenik()

#         for parohijan in parohijani[:5]:
#             self.create_random_krstenje(parohijan)

#         self.stdout.write(
#             self.style.SUCCESS("Успешно попуњена база података са насумичним уносима.")
#         )
