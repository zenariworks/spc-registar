"""
Migracija tabele `HSPKRST.sqlite` (tabele krstenja) u tabelu 'krstenja'
"""
import sqlite3
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from registar.models import Hram, Krstenje, Parohija, Ulica, Parohijan, Adresa
from registar.management.commands.convert_utils import ConvertUtils


from .unos_adresa import unesi_adresu

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

        # tabela 'opstine': Cukarica, Srbija
        #opstina_instance, _ = Opstina.objects.get_or_create(naziv="Чукарица")

        # tabela 'mesta': Cukarica
        #mesto_instance, _ =  Mesto.objects.get_or_create(naziv="Чукарица")

        # drzava_id 
        #drzava_instance, _ = unesi_drzavu("Србија")

        # Output the uids
        #print("opstina UID:", opstina_instance.uid)
        #print("mesto UID:", mesto_instance.uid)
        #print("drzava UID:", drzava_instance.uid)
       
        parsed_data = self._parse_data()
        created_count = 0

        for parohijan_uid, ime_prezime, ulica_uid, broj_ulice, \
            oznaka_ulice, broj_stana, telefon_fiksni, telefon_mobilni, \
            slava_uid, slavska_vodica, uskrsnja_vodica, napomena in parsed_data:
            try:
                adresa_instance = Adresa(
                    broj=broj_ulice,
                    dodatak=ConvertUtils.latin_to_cyrillic(oznaka_ulice),
                    postkod="",
                    primedba="",
                    ulica_id=Ulica.objects.get(uid=ulica_uid).uid
                )
                adresa_instance.save()

                # razdvoji ime i prezime" "ime prezime" -> ["ime", "prezime"]
                # i unesi kao ime i prezime
                ime_prezime = ime_prezime.split(" ")

                parohijan = Parohijan(
                    uid=parohijan_uid,
                    ime=ConvertUtils.latin_to_cyrillic(ime_prezime[0]),
                    prezime=ConvertUtils.latin_to_cyrillic(ime_prezime[1]),
                    mesto_rodjenja="",
                    datum_rodjenja=None,
                    vreme_rodjenja=None,
                    pol="",
                    devojacko_prezime="",
                    zanimanje="",
                    veroispovest="",
                    narodnost="",
                    adresa=adresa_instance,
                )
                parohijan.save()

                created_count += 1

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {e}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела 'ulice': {created_count} нових уноса."
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
            cursor.execute("SELECT dom_sifra, dom_ime, dom_rbrul, dom_broj, dom_oznaka, dom_stan, \
                           dom_teldir, dom_telmob, dom_rbrsl, dom_slavod, dom_uskvod, dom_napom   FROM HSPDOMACINI")
            rows = cursor.fetchall()

            for row in rows:
                parohijan_uid, ime_prezime, ulica_uid, broj_ulice, oznaka_ulice, broj_stana, telefon_fiksni, telefon_mobilni, slava_uid, slavska_vodica, uskrsnja_vodica, napomena = row
                parsed_data.append((parohijan_uid, ime_prezime, ulica_uid, broj_ulice, oznaka_ulice, broj_stana, telefon_fiksni, telefon_mobilni, slava_uid, slavska_vodica, uskrsnja_vodica, napomena))

        return parsed_data


#
# class Command(BaseCommand):
#     """
#     Класа Ђанго команде за попуњавање базе података насумичним парохијанима.
#     """

#     help = "Попуњава базу података насумичним парохијанима"

#     def random_parohijan(self, gender, min_age=0):
#         """Креира насумично парохијана."""
#         eligible_parohijan = Parohijan.objects.filter(
#             pol=gender,
#             datum_rodjenja__lte=date.today() - timedelta(days=min_age * 365.25),
#         )
#         if eligible_parohijan.exists():
#             return random.choice(eligible_parohijan)
#         else:
#             return RandomUtils.create_random_parohijan(unesi_adresu, gender, min_age)

#     def get_or_create_parohija(self, naziv):
#         """Креира насумично парохију."""
#         parohija, _ = Parohija.objects.get_or_create(naziv=naziv)
#         return parohija

#     def create_random_svestenik(self) -> Svestenik:
#         """Креира насумично свештеника."""
#         parohije = [
#             self.get_or_create_parohija("Парохија 1"),
#             self.get_or_create_parohija("Парохија 2"),
#             self.get_or_create_parohija("Парохија 3"),
#             self.get_or_create_parohija("Парохија 4"),
#         ]

#         svestenik = Svestenik(
#             zvanje=random.choice(RandomUtils.zvanja),
#             parohija=random.choice(parohije),
#             ime=random.choice(RandomUtils.male_names),
#             prezime=random.choice(RandomUtils.surnames),
#             mesto_rodjenja="Насумично место",
#             datum_rodjenja=RandomUtils.random_date_of_birth(25),
#         )
#         svestenik.save()
#         return svestenik

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
