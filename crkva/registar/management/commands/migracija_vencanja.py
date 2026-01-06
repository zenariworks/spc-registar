"""
Migracija tabele vencanja iz PostgreSQL staging tabele 'hsp_vencanja' u tabelu 'vencanja'
"""

from datetime import date
from typing import Optional, Tuple

from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.base_migration import MigrationCommand
from registar.management.commands.convert_utils import Konvertor
from registar.models import Hram, Osoba, Svestenik, Vencanje


class Command(MigrationCommand):
    help = "Migracija tabele vencanja iz PostgreSQL staging tabele 'hsp_vencanja'"
    staging_table_name = "hsp_vencanja"
    target_model = Vencanje

    # Serbian words for marriage order
    _MARRIAGE_ORDER = {
        1: "први",
        2: "други",
        3: "трећи",
        # Add more if needed in the future
    }

    def handle(self, *args, **kwargs):
        self.clear_target_table()
        records = self._fetch_and_parse_records()
        created_count = self._migrate_records(records)
        self.log_success(created_count, "венчања")
        self.drop_staging_table()

    def _fetch_and_parse_records(self):
        """Yield parsed records one by one from the staging table."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    "V_SIFRA", "V_AKTGOD",
                    "V_KNJIGA", "V_STRANA", "V_TEKBROJ",
                    "V_DATUM",
                    "V_Z_IME", "V_Z_PREZ", "V_Z_ZANIM", "V_Z_MESTO", "V_Z_VEROIS", "V_Z_NARODN", "V_Z_ADRESA",
                    "V_N_IME", "V_N_PREZ", "V_N_ZANIM", "V_N_MESTO", "V_N_VEROIS", "V_N_NARODN", "V_N_ADRESA",
                    "V_ZR_OTAC", "V_ZR_MAJKA", "V_NR_OTAC", "V_NR_MAJKA",
                    "V_Z_RODJG", "V_Z_RODJM", "V_Z_RODJD", "V_Z_RODJME",
                    "V_N_RODJG", "V_N_RODJM", "V_N_RODJD", "V_N_RODJME",
                    "V_Z_BRAK", "V_N_BRAK",
                    "V_ISPITGOD", "V_ISPITMES", "V_ISPITDAN",
                    "V_HRIME", "V_RBRSVEST",
                    "V_KUM", "V_SSVAT",
                    "V_RAZRDN", "V_RAZRTXT"
                FROM hsp_vencanja
                ORDER BY "V_SIFRA"
            """)
            for row in cursor.fetchall():
                yield self._parse_row(row)

    def _parse_row(self, row) -> Tuple:
        """Parse a raw DB row into cleaned values."""
        (
            redni_broj,
            godina,
            knjiga,
            strana,
            tekuci_broj,
            datum,
            z_ime,
            z_prez,
            z_zanim,
            z_mesto,
            z_vera,
            z_narod,
            z_adresa,
            n_ime,
            n_prez,
            n_zanim,
            n_mesto,
            n_vera,
            n_narod,
            n_adresa,
            z_otac,
            z_majka,
            n_otac,
            n_majka,
            z_godj,
            z_mesj,
            z_danj,
            z_mestoj,
            n_godj,
            n_mesj,
            n_danj,
            n_mestoj,
            z_brak,
            n_brak,
            ispit_god,
            ispit_mes,
            ispit_dan,
            hram_naziv,
            svestenik_id,
            kum_ime,
            svedok_ime,
            razresenje,
            razresenje_txt,
        ) = row

        def to_int(x, default):
            return Konvertor.int(x, default) if x is not None else default

        def to_str(x):
            return Konvertor.string(x or "")

        return (
            to_int(redni_broj, 0),
            to_int(godina, 1900),
            to_str(knjiga),
            to_str(strana),
            to_str(tekuci_broj),
            datum,  # already date or None
            to_str(z_ime),
            to_str(z_prez),
            to_str(z_zanim),
            to_str(z_mesto),
            to_str(z_vera),
            to_str(z_narod),
            to_str(z_adresa),
            to_str(n_ime),
            to_str(n_prez),
            to_str(n_zanim),
            to_str(n_mesto),
            to_str(n_vera),
            to_str(n_narod),
            to_str(n_adresa),
            to_str(z_otac),
            to_str(z_majka),
            to_str(n_otac),
            to_str(n_majka),
            to_int(z_godj, 0),
            to_int(z_mesj, 0),
            to_int(z_danj, 0),
            to_str(z_mestoj),
            to_int(n_godj, 0),
            to_int(n_mesj, 0),
            to_int(n_danj, 0),
            to_str(n_mestoj),
            to_int(z_brak, 1),
            to_int(n_brak, 1),
            to_int(ispit_god, 0),
            to_int(ispit_mes, 0),
            to_int(ispit_dan, 0),
            to_str(hram_naziv),
            to_int(svestenik_id, 0),
            to_str(kum_ime),
            to_str(svedok_ime),
            to_str(razresenje),
            to_str(razresenje_txt),
        )

    def _migrate_records(self, records):
        created_count = 0
        for record in records:
            try:
                data = self._build_vencanje_data(record)
                if data is None:
                    continue
                Vencanje.objects.create(**data)
                created_count += 1
            except IntegrityError as e:
                self.log_error(e)
            except Exception as e:
                self.log_error(f"Neočekivana greška: {e}")
        return created_count

    def _build_vencanje_data(self, data: Tuple) -> Optional[dict]:
        (
            redni_broj,
            godina,
            knjiga,
            strana,
            tekuci_broj,
            datum,
            z_ime,
            z_prez,
            z_zanim,
            z_mesto,
            z_vera,
            z_narod,
            z_adresa,
            n_ime,
            n_prez,
            n_zanim,
            n_mesto,
            n_vera,
            n_narod,
            n_adresa,
            z_otac,
            z_majka,
            n_otac,
            n_majka,
            z_godj,
            z_mesj,
            z_danj,
            z_mestoj,
            n_godj,
            n_mesj,
            n_danj,
            n_mestoj,
            z_brak,
            n_brak,
            ispit_god,
            ispit_mes,
            ispit_dan,
            hram_naziv,
            svestenik_id,
            kum_ime,
            svedok_ime,
            razresenje,
            razresenje_txt,
        ) = data

        # Skip invalid core records
        if not z_ime or not z_prez or not n_ime or not n_prez:
            self.log_warning(
                f"Прескачем венчање без имена/презимена: "
                f"женик '{z_ime} {z_prez}', невеста '{n_ime} {n_prez}'"
            )
            return None

        # Fix zero dates → default to 1900-01-01
        z_godj, z_mesj, z_danj = self._fix_zero_date(z_godj, z_mesj, z_danj)
        n_godj, n_mesj, n_danj = self._fix_zero_date(n_godj, n_mesj, n_danj)
        ispit_god, ispit_mes, ispit_dan = self._fix_zero_date(
            ispit_god, ispit_mes, ispit_dan
        )

        datum_rodj_zenik = date(z_godj, z_mesj, z_danj)
        datum_rodj_nevesta = date(n_godj, n_mesj, n_danj)
        datum_ispita = date(ispit_god, ispit_mes, ispit_dan)

        # Related objects
        hram = Hram.objects.get_or_create(naziv=Konvertor.string(hram_naziv))[0]
        svestenik = Svestenik.objects.get_or_create(uid=svestenik_id)[0]

        # Persons
        zenik = self._find_or_create_osoba(
            z_ime,
            z_prez,
            datum_rodjenja=datum_rodj_zenik,
            mesto_rodjenja=z_mestoj,
            pol="М",
            zanimanje=z_zanim,
            veroispovest=z_vera,
            narodnost=z_narod,
        )

        nevesta = self._find_or_create_osoba(
            n_ime,
            n_prez,
            datum_rodjenja=datum_rodj_nevesta,
            mesto_rodjenja=n_mestoj,
            pol="Ж",
            zanimanje=n_zanim,
            veroispovest=n_vera,
            narodnost=n_narod,
        )

        kum = None
        if kum_ime.strip():
            kum_ime_clean, kum_prezime = self._split_full_name(kum_ime.strip())
            if kum_ime_clean and kum_prezime:
                kum = self._find_or_create_osoba(kum_ime_clean, kum_prezime)
            else:
                self.log_warning(f"Кум није могао бити раздвојен: '{kum_ime}'")

        return {
            # Relations
            "zenik": zenik,
            "nevesta": nevesta,
            "kum": kum,
            "hram": hram,
            "svestenik": svestenik,
            # Registry info
            "redni_broj_vencanja_tekuca_godina": redni_broj,
            "vencanje_tekuca_godina": godina,
            "knjiga": Konvertor.int(knjiga, 0),
            "strana": Konvertor.int(strana, 0),
            "tekuci_broj": Konvertor.int(tekuci_broj, 0),
            "datum": datum,
            # Groom
            "ime_zenika": z_ime,
            "prezime_zenika": z_prez,
            "zanimanje_zenika": z_zanim,
            "mesto_zenika": z_mesto,
            "veroispovest_zenika": z_vera,
            "narodnost_zenika": z_narod,
            "adresa_zenika": z_adresa,
            "svekar": z_otac,
            "svekrva": z_majka,
            "datum_rodjenja_zenika": datum_rodj_zenik,
            "mesto_rodjenja_zenika": z_mestoj,
            "zenik_rb_brak": self._marriage_order_word(z_brak),
            # Bride
            "ime_neveste": n_ime,
            "prezime_neveste": n_prez,
            "zanimanje_neveste": n_zanim,
            "mesto_neveste": n_mesto,
            "veroispovest_neveste": n_vera,
            "narodnost_neveste": n_narod,
            "adresa_neveste": n_adresa,
            "tast": n_otac,
            "tasta": n_majka,
            "datum_rodjenja_neveste": datum_rodj_nevesta,
            "mesto_rodjenja_neveste": n_mestoj,
            "nevesta_rb_brak": self._marriage_order_word(n_brak),
            # Other
            "datum_ispita": datum_ispita,
            "ime_kuma": kum_ime,
            "stari_svat": svedok_ime,
            "razresenje": "нису" if razresenje.strip() == "N" else "јесу",
            "razresenje_primedba": razresenje_txt,
            "primedba": "",
        }

    def _fix_zero_date(self, year: int, month: int, day: int) -> Tuple[int, int, int]:
        """Replace 0 values with safe defaults (1900-01-01)."""
        return (
            1900 if year == 0 else year,
            1 if month == 0 else month,
            1 if day == 0 else day,
        )

    def _marriage_order_word(self, num: int) -> str:
        """Convert marriage order number to Serbian word ('први', 'други', ...)."""
        return self._MARRIAGE_ORDER.get(num, "први")  # default to "први" if unknown

    @staticmethod
    def _split_full_name(full_name: str) -> Tuple[str, str]:
        """Split full name into first name(s) and surname (last word)."""
        parts = full_name.strip().split()
        if len(parts) < 2:
            return full_name, ""
        return " ".join(parts[:-1]), parts[-1]

    def _find_or_create_osoba(
        self, ime: str, prezime: str, **extra_fields
    ) -> Optional[Osoba]:
        """Find or create Osoba, updating missing fields if found."""
        if not ime or not prezime:
            return None

        ime, prezime = ime.strip(), prezime.strip()
        if not ime or not prezime:
            return None

        osoba = Osoba.objects.filter(ime__exact=ime, prezime__exact=prezime).first()
        if osoba:
            updated = False
            for field, value in extra_fields.items():
                if value and not getattr(osoba, field, None):
                    setattr(osoba, field, value)
                    updated = True
            if updated:
                osoba.save(update_fields=extra_fields.keys())
            return osoba

        create_kwargs = {"ime": ime, "prezime": prezime, "parohijan": False}
        create_kwargs.update({k: v for k, v in extra_fields.items() if v is not None})
        return Osoba.objects.create(**create_kwargs)
