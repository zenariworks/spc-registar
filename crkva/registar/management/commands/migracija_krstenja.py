"""
Migracija tabele krstenja iz PostgreSQL staging tabele 'hsp_krstenja' u tabelu 'krstenja'
"""

import re
from dataclasses import dataclass
from datetime import date, time
from typing import Optional, Tuple

from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.base_migration import MigrationCommand
from registar.management.commands.convert_utils import Konvertor
from registar.models import Hram, Krstenje, Osoba, Svestenik


@dataclass
class KrstenjeRecord:
    """Clean, typed representation of one row from hsp_krstenja"""

    redni_broj: int
    knjiga: str
    broj: str
    strana: int

    adresa_deteta_grad: str
    adresa_deteta_ulica: str
    adresa_deteta_broj: str

    rodjenje_godina: int
    rodjenje_mesec: int
    rodjenje_dan: int
    rodjenje_vreme: str
    rodjenje_mesto: str

    krstenje_godina: int
    krstenje_mesec: int
    krstenje_dan: int
    krstenje_vreme: str
    krstenje_mesto: str
    hram_naziv: str

    dete_ime: str
    dete_gradjansko_ime: str
    dete_pol: str

    otac_ime: str
    otac_prezime: str
    otac_zanimanje: str
    otac_adresa: str
    otac_veroispovest: str
    otac_narodnost: str

    majka_ime: str
    majka_prezime: str
    majka_zanimanje: str
    majka_adresa: str
    majka_veroispovest: str

    dete_rodjeno_zivo: str
    dete_po_redu_po_majci: int
    dete_vanbracno: str
    dete_blizanac: str
    blizanac_ime: str
    dete_sa_manom: str

    svestenik_id: int

    kum_puno_ime: str
    kum_prezime: str
    kum_zanimanje: str
    kum_mesto: str

    registracija_mesto: str
    registracija_datum: Optional[date]
    registracija_broj: Optional[str]
    registracija_strana: Optional[str]


class Command(MigrationCommand):
    help = "Migracija tabele krstenja iz PostgreSQL staging tabele 'hsp_krstenja'"
    staging_table_name = "hsp_krstenja"
    target_model = Krstenje

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
        records = list(self._fetch_records())
        created_count = self._migrate_records(records)
        self.log_success(created_count, "крштења")
        self.drop_staging_table()

    def _fetch_records(self):
        """Yield parsed KrstenjeRecord objects from staging table."""
        with connection.cursor() as cursor:
            cursor.execute(f"""
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
                FROM {self.staging_table_name}
                ORDER BY "K_SIFRA"
            """)
            for row in cursor.fetchall():
                yield self._parse_record(row)

    def _parse_record(self, row) -> KrstenjeRecord:
        """Convert raw DB row to clean KrstenjeRecord."""

        def s(v):
            return Konvertor.string(v or "")

        def i(v, default=0):
            return Konvertor.int(v, default) if v is not None else default

        return KrstenjeRecord(
            redni_broj=i(row[0], 0),
            knjiga=s(row[1]),
            broj=s(row[2]),
            strana=i(row[3], 0),
            adresa_deteta_grad=s(row[4]),
            adresa_deteta_ulica=s(row[5]),
            adresa_deteta_broj=s(row[6]),
            rodjenje_godina=i(row[7], 1900),
            rodjenje_mesec=i(row[8], 1),
            rodjenje_dan=i(row[9], 1),
            rodjenje_vreme=s(row[10]),
            rodjenje_mesto=s(row[11]),
            krstenje_godina=i(row[12], 1900),
            krstenje_mesec=i(row[13], 1),
            krstenje_dan=i(row[14], 1),
            krstenje_vreme=s(row[15]),
            krstenje_mesto=s(row[16]),
            hram_naziv=s(row[17]),
            dete_ime=s(row[18]),
            dete_gradjansko_ime=s(row[19]),
            dete_pol=s(row[20]),
            otac_ime=s(row[21]),
            otac_prezime=s(row[22]),
            otac_zanimanje=s(row[23]),
            otac_adresa=s(row[24]),
            otac_veroispovest=s(row[25]),
            otac_narodnost=s(row[26]),
            majka_ime=s(row[27]),
            majka_prezime=s(row[28]),
            majka_zanimanje=s(row[29]),
            majka_adresa=s(row[30]),
            majka_veroispovest=s(row[31]),
            dete_rodjeno_zivo=s(row[32]),
            dete_po_redu_po_majci=i(row[33], 1),
            dete_vanbracno=s(row[34]),
            dete_blizanac=s(row[35]),
            blizanac_ime=s(row[36]),
            dete_sa_manom=s(row[37]),
            svestenik_id=i(row[38], 0),
            kum_puno_ime=s(row[39]),
            kum_prezime=s(row[40]),
            kum_zanimanje=s(row[41]),
            kum_mesto=s(row[42]),
            registracija_mesto=s(row[43]),
            registracija_datum=row[44],
            registracija_broj=row[45],
            registracija_strana=row[46],
        )

    def _migrate_records(self, records):
        created_count = 0
        for record in records:
            try:
                data = self._build_krstenje(record)
                if data is None:
                    continue
                Krstenje.objects.create(**data)
                created_count += 1
            except IntegrityError as e:
                self.log_error(e)
            except Exception as e:
                self.log_error(f"Unexpected error: {e}")
        return created_count

    def _build_krstenje(self, r: KrstenjeRecord) -> Optional[dict]:
        if not r.dete_ime.strip() or not r.otac_prezime.strip():
            self.log_warning("Прескачем запис без имена детета или презимена оца")
            return None

        datum_krstenja = date(r.krstenje_godina, r.krstenje_mesec, r.krstenje_dan)
        vreme_krstenja = self._parse_time(r.krstenje_vreme)

        # Related objects
        hram_naziv_clean = re.sub(r"(?i)\bhram\b", "", r.hram_naziv).strip()
        hram, _ = Hram.objects.get_or_create(naziv=Konvertor.string(hram_naziv_clean))

        svestenik, _ = Svestenik.objects.get_or_create(uid=r.svestenik_id)

        # Persons
        dete = self._find_or_create_osoba(
            ime=r.dete_ime.strip(),
            prezime=r.otac_prezime.strip(),
            pol="М" if r.dete_pol.strip() == "1" else "Ж",
            datum_rodjenja=date(r.rodjenje_godina, r.rodjenje_mesec, r.rodjenje_dan),
            vreme_rodjenja=self._parse_time(r.rodjenje_vreme),
            mesto_rodjenja=r.rodjenje_mesto,
        )

        otac = self._find_or_create_osoba(
            ime=r.otac_ime.strip(),
            prezime=r.otac_prezime.strip(),
            pol="М",
            zanimanje=r.otac_zanimanje,
            veroispovest=r.otac_veroispovest,
            narodnost=r.otac_narodnost,
        )

        majka = self._find_or_create_osoba(
            ime=r.majka_ime.strip(),
            prezime=r.majka_prezime.strip(),
            pol="Ж",
            zanimanje=r.majka_zanimanje,
            veroispovest=r.majka_veroispovest,
        )

        kum = None
        if kum_puno_ime := r.kum_puno_ime.strip():
            # Use K_KUMPREZ if available, otherwise split from full name
            if kum_prezime := r.kum_prezime.strip():
                kum_ime = kum_puno_ime
            else:
                kum_ime, kum_prezime = self._split_full_name(kum_puno_ime)

            if kum_ime and kum_prezime:
                kum = self._find_or_create_osoba(
                    ime=kum_ime,
                    prezime=kum_prezime,
                    zanimanje=r.kum_zanimanje,
                )
            else:
                self.log_warning(f"Неуспело цепање имена кума: '{kum_puno_ime}'")

        gradjansko_sufiks = (
            f" (грађанско {r.dete_gradjansko_ime})"
            if r.dete_gradjansko_ime.strip()
            else ""
        )

        return {
            "dete": dete,
            "otac": otac,
            "majka": majka,
            "kum": kum,
            "hram": hram,
            "svestenik": svestenik,
            "redni_broj_krstenja_tekuca_godina": r.redni_broj,
            "krstenje_tekuca_godina": r.krstenje_godina,
            "knjiga": Konvertor.int(r.knjiga, 0),
            "broj": Konvertor.int(r.broj, 0),
            "strana": Konvertor.int(r.strana, 0),
            "datum": datum_krstenja,
            "vreme": vreme_krstenja,
            "mesto": r.krstenje_mesto,
            "adresa_deteta_grad": r.adresa_deteta_grad,
            "adresa_deteta_ulica": r.adresa_deteta_ulica,
            "adresa_deteta_broj": r.adresa_deteta_broj,
            "gradjansko_ime_deteta": gradjansko_sufiks,
            "adresa_oca_mesto": r.otac_adresa,
            "adresa_majke_mesto": r.majka_adresa,
            "dete_rodjeno_zivo": r.dete_rodjeno_zivo.strip() == "1",
            "dete_po_redu_po_majci": self._ordinal_word(r.dete_po_redu_po_majci),
            "dete_vanbracno": r.dete_vanbracno.strip() == "1",
            "dete_blizanac": r.dete_blizanac.strip() == "1",
            "drugo_dete_blizanac_ime": r.blizanac_ime,
            "dete_sa_telesnom_manom": r.dete_sa_manom.strip() == "1",
            "adresa_kuma_mesto": r.kum_mesto,
            "mesto_registracije": r.registracija_mesto,
            "datum_registracije": r.registracija_datum,
            "maticni_broj": r.registracija_broj,
            "strana_registracije": r.registracija_strana,
            "primedba": "",
        }

    def _parse_time(self, time_str: str) -> Optional[time]:
        if not (time_str := str(time_str or "").strip()):
            return None

        if "." in time_str or "," in time_str:
            sep = "." if "." in time_str else ","
            parts = time_str.split(sep)
            hh = Konvertor.int(parts[0], 12)
            mm = Konvertor.int(parts[1], 0) if len(parts) > 1 else 0
        else:
            hh = Konvertor.int(time_str, 12)
            mm = 0

        hh = 0 if hh == 24 else max(0, min(23, hh))
        mm = max(0, min(59, mm))
        return time(hh, mm)

    def _ordinal_word(self, num: int) -> str:
        return self._ORDINAL_WORDS[num - 1] if 1 <= num <= 10 else "прво"

    @staticmethod
    def _split_full_name(full_name: str) -> Tuple[str, str]:
        parts = full_name.strip().split()
        return (" ".join(parts[:-1]), parts[-1]) if len(parts) >= 2 else (full_name, "")

    def _find_or_create_osoba(self, ime: str, prezime: str, **extra) -> Optional[Osoba]:
        if not ime or not prezime:
            return None

        osoba = Osoba.objects.filter(ime__exact=ime, prezime__exact=prezime).first()
        if osoba:
            updates = {
                k: v for k, v in extra.items() if v and not getattr(osoba, k, None)
            }
            if updates:
                Osoba.objects.filter(pk=osoba.pk).update(**updates)
                osoba.refresh_from_db()
            return osoba

        create_data = {"ime": ime, "prezime": prezime, "parohijan": False}
        create_data.update({k: v for k, v in extra.items() if v is not None})
        return Osoba.objects.create(**create_data)
