"""
Migracija tabele `HSPKRST.sqlite` (tabele krstenja) u tabelu 'krstenja'
"""
import sqlite3
from django.core.management.base import BaseCommand
from registar.models import Hram, Krstenje, Parohija, Ulica, Parohijan, Adresa, Slava
from registar.management.commands.convert_utils import ConvertUtils
from django.db.utils import IntegrityError

from .unos_adresa import unesi_adresu

class Command(BaseCommand):
    """
    Класа Ђанго команде за попуњавање табеле 'parohijani'

    cmd:
    docker compose run --rm app sh -c "python manage.py migracija_parohijana"
    """
    help = "Migracija tabele `HSPDOMACINI.sqlite` (tabela domacina) u tabele: 'adrese', 'parohijani'"

    def handle(self, *args, **kwargs):

        parsed_data = self._parse_data()
        created_count = 0

        for parohijan_uid, ime_prezime, ulica_uid, broj_ulice, oznaka_ulice, broj_stana, \
            telefon_fiksni, telefon_mobilni, slava_uid, slavska_vodica, uskrsnja_vodica, napomena in parsed_data:
            try:
                # print("ulica_uid: " + str(ulica_uid)) 
                # uid=Ulica.objects.get(uid=ulica_uid).uid,
                # print("uid: " + str(uid)) 
                # print("slavska_vodica: " + slavska_vodica) 

                # if type(slava_uid) == int:
                #     print("slava_uid is an integer.")
                # elif type(slava_uid) == str:
                #     print("slava_uid is a string.")
                
                # tabela 'adrese'
                adresa_instance = Adresa(
                    broj=broj_ulice,
                    sprat=None,
                    broj_stana=broj_stana,
                    dodatak=ConvertUtils.latin_to_cyrillic(oznaka_ulice),
                    postkod=None,
                    primedba=ConvertUtils.latin_to_cyrillic(napomena),
                    ulica=Ulica.objects.get(uid=ulica_uid)
                )
                adresa_instance.save()

                # tabela 'parohijani'
                # razdvoji ime i prezime" "ime prezime" -> ["ime", "prezime"]
                # i unesi kao ime i prezime
                ime_prezime = ime_prezime.split(" ")

                parohijan = Parohijan(
                    uid=parohijan_uid,
                    ime=ConvertUtils.latin_to_cyrillic(ime_prezime[0]),
                    prezime=ConvertUtils.latin_to_cyrillic(ime_prezime[1]),
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
                    narodnost=None
                )
                parohijan.save()

                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'parohijani': {created_count} нових уноса."
            )
        )

    def _parse_data(self):
        """
        Migracija tabele 'HSPDOMACINI.sqlite' 
            dom_sifra       - parohijan_uid, 
            dom_ime         - ime i prezime
            dom_rbrul       - ulica_id  (npr. Radnicka je 22)
            dom_broj        - broj ulice (npr. 42)
            dom_oznaka      - oznaka ulice (npr. A, B, C)
            dom_stan        - broj stana (npr. 12)
            dom_teldir      - telefon fiksni
            dom_telmob      - telefon mobilni
            dom_rbrsl       - slava_id (npr. Sveti Jovan Krstitelj je 20)
            dom_slavod      - slavska vodica (true/false - da li svestenik dolazi da sveti slavsku vodicu)
            dom_uskvod      - uskrsnja vodica (true/false - da li svestenik dolazi da sveti vodicu uoci Uskrsa)
            dom_napom       - napomena (opciono)

        :return: Листа парсираних података ( ... )
        """
        parsed_data = []
        with sqlite3.connect("fixtures/combined_original_hsp_database.sqlite") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dom_rbr, dom_ime, dom_rbrul, dom_broj, dom_oznaka, dom_stan, \
                           dom_teldir, dom_telmob, dom_rbrsl, dom_slavod, dom_uskvod, dom_napom FROM HSPDOMACINI")
            rows = cursor.fetchall()

            for row in rows:
                parohijan_uid, ime_prezime, ulica_uid, broj_ulice, oznaka_ulice, broj_stana, telefon_fiksni, \
                    telefon_mobilni, slava_uid, slavska_vodica, uskrsnja_vodica, napomena = row
                parsed_data.append((parohijan_uid, ime_prezime, ulica_uid, broj_ulice, oznaka_ulice, broj_stana, telefon_fiksni, \
                                    telefon_mobilni, slava_uid, slavska_vodica, uskrsnja_vodica, napomena))

        return parsed_data

