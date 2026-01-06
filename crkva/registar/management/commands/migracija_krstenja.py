"""
Migracija tabele krstenja iz PostgreSQL staging tabele 'hsp_krstenja' u tabelu 'krstenja'
"""

import re
from datetime import date, time
from typing import Optional, Tuple

from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.base_migration import MigrationCommand
from registar.management.commands.convert_utils import Konvertor
from registar.models import Hram, Krstenje, Osoba, Svestenik


class Command(MigrationCommand):
    help = "Migracija tabele krstenja iz PostgreSQL staging tabele 'hsp_krstenja'"
    staging_table_name = "hsp_krstenja"
    target_model = Krstenje

    # Serbian ordinal words for child order (1st to 10th)
    _ORDINAL_WORDS = [
        "прво",
        "друго",
        "треће",
        "четврто",
        "пето",
        "шесто",
        "седмо",
        "осмо",
        "девето",
        "десето",
    ]

    def handle(self, *args, **kwargs):
        self.clear_target_table()
        records = self._fetch_and_parse_records()
        created_count = self._migrate_records(records)
        self.log_success(created_count, "крштења")
        self.drop_staging_table()

    def _fetch_and_parse_records(self):
        """Fetch all rows from staging table and parse them into clean tuples."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    "K_SIFRA", "K_PROKNJ", "K_PROTBR", "K_PROTST",
                    "K_IZ", "K_ULICA", "K_BROJ",
                    "K_RODJGOD", "K_RODJMESE", "K_RODJDAN", "K_RODJVRE", "K_RODJMEST",
                    "K_KRSGOD", "K_KRSMESE", "K_KRSDAN", "K_KRSVRE", "K_KRSMEST", "K_KRSHRAM",
                    "K_DETIME", "K_DETIMEG", "K_DETPOL",
                    "K_RODIME", "K_RODPREZ", "K_RODZANIM", "K_RODMEST", "K_RODVERA", "K_RODNAROD",
                    "K_ROD2IME", "K_ROD2PREZ", "K_ROD2ZAN", "K_ROD2MEST", "K_ROD2VERA",
                    "K_DETZIVO", "K_DETKOJE", "K_DETBRAC", "K_DETBLIZ", "K_DETBLIZ2", "K_DETMANA",
                    "K_RBRSVE",
                    "K_KUMIME", "K_KUMPREZ", "K_KUMZANIM", "K_KUMMEST",
                    "K_REGMESTO", "K_REGKADA", "K_REGBROJ", "K_REGSTR"
                FROM hsp_krstenja
                ORDER BY "K_SIFRA"
            """)
            rows = cursor.fetchall()

        for row in rows:
            yield self._parse_row(row)

    def _parse_row(self, row) -> Tuple:
        """Convert a raw database row into a cleaned tuple of values."""
        (
            redni_broj,
            knjiga,
            broj,
            strana,
            adr_grad,
            adr_ulica,
            adr_broj,
            r_god,
            r_mes,
            r_dan,
            r_vreme,
            r_mesto,
            k_god,
            k_mes,
            k_dan,
            k_vreme,
            k_mesto,
            hram_naziv,
            ime_d,
            gradj_ime_d,
            pol_d,
            ime_o,
            prez_o,
            zan_o,
            adr_o,
            vera_o,
            narod_o,
            ime_m,
            prez_m,
            zan_m,
            adr_m,
            vera_m,
            zivo,
            red_po_majci,
            vanbracno,
            blizanac,
            bliz_ime,
            mana,
            svestenik_id,
            kum_puno,
            kum_prez,
            kum_zan,
            kum_mesto,
            reg_mesto,
            reg_datum,
            reg_broj,
            reg_strana,
        ) = row

        # Helper to safely convert to int with fallback
        def to_int(x, default):
            return Konvertor.int(x, default) if x is not None else default

        def to_str(x):
            return Konvertor.string(x or "")

        return (
            to_int(redni_broj, 0),
            to_str(knjiga),
            to_str(broj),
            to_int(strana, 0),
            to_str(adr_grad),
            to_str(adr_ulica),
            to_str(adr_broj),
            to_int(r_god, 1900),
            to_int(r_mes, 1),
            to_int(r_dan, 1),
            to_str(r_vreme),
            to_str(r_mesto),
            to_int(k_god, 1900),
            to_int(k_mes, 1),
            to_int(k_dan, 1),
            to_str(k_vreme),
            to_str(k_mesto),
            to_str(hram_naziv),
            to_str(ime_d),
            to_str(gradj_ime_d),
            to_str(pol_d),
            to_str(ime_o),
            to_str(prez_o),
            to_str(zan_o),
            to_str(adr_o),
            to_str(vera_o),
            to_str(narod_o),
            to_str(ime_m),
            to_str(prez_m),
            to_str(zan_m),
            to_str(adr_m),
            to_str(vera_m),
            to_str(zivo),
            to_int(red_po_majci, 1),
            to_str(vanbracno),
            to_str(blizanac),
            to_str(bliz_ime),
            to_str(mana),
            to_int(svestenik_id, 0),
            to_str(kum_puno),
            to_str(kum_prez),
            to_str(kum_zan),
            to_str(kum_mesto),
            to_str(reg_mesto),
            reg_datum,
            reg_broj,
            reg_strana,
        )

    def _migrate_records(self, records):
        """Process parsed records and create Krstenje instances."""
        created_count = 0

        for record in records:
            try:
                krstenje_data = self._build_krstenje(record)
                if krstenje_data is None:
                    continue  # Skip invalid records

                Krstenje.objects.create(**krstenje_data)
                created_count += 1

            except IntegrityError as e:
                self.log_error(e)
            except Exception as e:
                self.log_error(f"Unexpected error: {e}")

        return created_count

    def _build_krstenje(self, zapis: Tuple) -> Optional[dict]:
        """Build a dictionary suitable for Krstenje.objects.create()."""
        (
            redni_broj,
            knjiga,
            broj,
            strana,
            adr_grad,
            adr_ulica,
            adr_broj,
            r_god,
            r_mes,
            r_dan,
            r_vreme,
            r_mesto,
            k_god,
            k_mes,
            k_dan,
            k_vreme,
            k_mesto,
            hram_naziv,
            ime_d,
            gradj_ime_d,
            pol_d,
            ime_o,
            prez_o,
            zan_o,
            adr_o,
            vera_o,
            narod_o,
            ime_m,
            prez_m,
            zan_m,
            adr_m,
            vera_m,
            zivo,
            red_po_majci,
            vanbracno,
            blizanac,
            bliz_ime,
            mana,
            svestenik_id,
            kum_puno,
            kum_prez,
            kum_zan,
            kum_mesto,
            reg_mesto,
            reg_datum,
            reg_broj,
            reg_strana,
        ) = zapis

        # Basic validation
        if not ime_d or not prez_o:
            self.log_warning(
                f"Прескачем запис без имена детета или презимена оца: {ime_d} {prez_o}"
            )
            return None

        # Dates and times
        datum_krstenja = date(k_god, k_mes, k_dan)
        vreme_krstenja = self._parse_time(k_vreme)

        datum_rodjenja = date(r_god, r_mes, r_dan)
        vreme_rodjenja = self._parse_time(r_vreme)

        # Related objects
        hram_clean = re.sub(r"(?i)\bhram\b", "", hram_naziv).strip()
        hram, _ = Hram.objects.get_or_create(naziv=Konvertor.string(hram_clean))

        svestenik, _ = Svestenik.objects.get_or_create(uid=svestenik_id)

        # Persons
        dete = self._find_or_create_osoba(
            ime_d,
            prez_o,
            datum_rodjenja=datum_rodjenja,
            mesto_rodjenja=Konvertor.string(r_mesto),
            pol="М" if pol_d.rstrip() == "1" else "Ж",
        )

        otac = self._find_or_create_osoba(
            ime_o,
            prez_o,
            zanimanje=Konvertor.string(zan_o),
            veroispovest=Konvertor.string(vera_o),
            narodnost=Konvertor.string(narod_o),
        )

        majka = self._find_or_create_osoba(
            ime_m,
            prez_m,
            zanimanje=Konvertor.string(zan_m),
            veroispovest=Konvertor.string(vera_m),
            pol="Ж",
        )

        kum = None
        if kum_puno.strip():
            kum_ime, kum_prezime = self._split_full_name(kum_puno.strip())
            if kum_ime and kum_prezime:
                kum = self._find_or_create_osoba(
                    kum_ime, kum_prezime, zanimanje=Konvertor.string(kum_zan)
                )
            else:
                self.log_warning(f"Неуспело цепање имена кума: '{kum_puno}'")

        # Gradjansko ime
        gradj_sufix = (
            f" (грађанско {Konvertor.string(gradj_ime_d)})" if gradj_ime_d else ""
        )

        return {
            # Relations
            "dete": dete,
            "otac": otac,
            "majka": majka,
            "kum": kum,
            "hram": hram,
            "svestenik": svestenik,
            # Basic info
            "redni_broj_krstenja_tekuca_godina": redni_broj,
            "krstenje_tekuca_godina": k_god,
            "knjiga": Konvertor.int(knjiga, 0),
            "broj": Konvertor.int(broj, 0),
            "strana": Konvertor.int(strana, 0),
            # Baptism details
            "datum": datum_krstenja,
            "vreme": vreme_krstenja,
            "mesto": Konvertor.string(k_mesto),
            # Child address
            "adresa_deteta_grad": adr_grad,
            "adresa_deteta_ulica": adr_ulica,
            "adresa_deteta_broj": adr_broj,
            # Birth details
            "datum_rodjenja": datum_rodjenja,
            "vreme_rodjenja": vreme_rodjenja,
            "mesto_rodjenja": Konvertor.string(r_mesto),
            # Child name
            "ime_deteta": Konvertor.string(ime_d),
            "gradjansko_ime_deteta": gradj_sufix,
            "pol_deteta": "М" if pol_d.rstrip() == "1" else "Ж",
            # Parents
            "ime_oca": ime_o,
            "prezime_oca": prez_o,
            "zanimanje_oca": zan_o,
            "adresa_oca_mesto": adr_o,
            "veroispovest_oca": vera_o,
            "narodnost_oca": narod_o,
            "ime_majke": ime_m,
            "prezime_majke": prez_m,
            "zanimanje_majke": zan_m,
            "adresa_majke_mesto": adr_m,
            "veroispovest_majke": vera_m,
            # Other child flags
            "dete_rodjeno_zivo": zivo.rstrip() == "1",
            "dete_po_redu_po_majci": self._ordinal_word(red_po_majci),
            "dete_vanbracno": vanbracno.rstrip() == "1",
            "dete_blizanac": blizanac.rstrip() == "1",
            "drugo_dete_blizanac_ime": Konvertor.string(bliz_ime),
            "dete_sa_telesnom_manom": mana.rstrip() == "1",
            # Godparent
            "ime_kuma": kum_puno,
            "prezime_kuma": kum_prez,
            "zanimanje_kuma": kum_zan,
            "adresa_kuma_mesto": kum_mesto,
            # Registry
            "mesto_registracije": Konvertor.string(reg_mesto),
            "datum_registracije": reg_datum or None,
            "maticni_broj": reg_broj or None,
            "strana_registracije": reg_strana or None,
            "primedba": "",
        }

    def _parse_time(self, time_str: str) -> Optional[time]:
        """Parse time string in formats like '14.30', '14,30', or '14'."""
        if not time_str or not str(time_str).strip():
            return None

        time_str = str(time_str).strip()
        hh, mm = 12, 0

        if "." in time_str or "," in time_str:
            separator = "." if "." in time_str else ","
            parts = time_str.split(separator)
            hh = Konvertor.int(parts[0], 12)
            mm = Konvertor.int(parts[1], 0) if len(parts) > 1 else 0
        else:
            hh = Konvertor.int(time_str, 12)

        # Basic correction
        if hh == 24:
            hh = 0
        hh = max(0, min(23, hh))
        mm = max(0, min(59, mm))

        return time(hh, mm)

    def _ordinal_word(self, num: int) -> str:
        """Convert number 1–10 to Serbian ordinal string."""
        return self._ORDINAL_WORDS[num - 1] if 1 <= num <= 10 else "прво"

    @staticmethod
    def _split_full_name(full_name: str) -> Tuple[str, str]:
        """Simple split: last word = surname, rest = first name."""
        parts = full_name.strip().split()
        if len(parts) < 2:
            return full_name, ""
        return " ".join(parts[:-1]), parts[-1]

    def _find_or_create_osoba(
        self, ime: str, prezime: str, **extra_fields
    ) -> Optional[Osoba]:
        """Find existing Osoba or create new one, updating missing fields."""
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

        # Filter out empty extra fields
        create_kwargs = {"ime": ime, "prezime": prezime, "parohijan": False}
        create_kwargs.update({k: v for k, v in extra_fields.items() if v is not None})
        return Osoba.objects.create(**create_kwargs)
