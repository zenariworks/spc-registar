"""
Migracija tabele vencanja iz PostgreSQL staging tabele 'hsp_vencanja' u tabelu 'vencanja'
"""

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional, Tuple

from django.db import connection
from django.db.utils import IntegrityError
from registar.management.commands.base_migration import MigrationCommand
from registar.management.commands.convert_utils import Konvertor
from registar.models import Hram, Osoba, Svestenik, Vencanje


@dataclass
class VencanjeRecord:
    """Structured representation of a row from hsp_vencanja"""

    redni_broj: int
    godina: int

    knjiga: str
    strana: str
    tekuci_broj: str

    datum: Optional[date]

    zenik_ime: str
    zenik_prezime: str
    zenik_zanimanje: str
    zenik_mesto: str
    zenik_veroispovest: str
    zenik_narodnost: str
    zenik_adresa: str

    nevesta_ime: str
    nevesta_prezime: str
    nevesta_zanimanje: str
    nevesta_mesto: str
    nevesta_veroispovest: str
    nevesta_narodnost: str
    nevesta_adresa: str

    svekar: str
    svekrva: str
    tast: str
    tasta: str

    zenik_god_rodj: int
    zenik_mes_rodj: int
    zenik_dan_rodj: int
    zenik_mesto_rodj: str

    nevesta_god_rodj: int
    nevesta_mes_rodj: int
    nevesta_dan_rodj: int
    nevesta_mesto_rodj: str

    zenik_rb_braka: int
    nevesta_rb_braka: int

    ispit_godina: int
    ispit_mesec: int
    ispit_dan: int

    hram_naziv: str
    svestenik_id: int

    kum_puno_ime: str
    stari_svat: str

    razresenje: str
    razresenje_txt: str


class Command(MigrationCommand):
    help = "Migracija tabele vencanja iz PostgreSQL staging tabele 'hsp_vencanja'"
    staging_table_name = "hsp_vencanja"
    target_model = Vencanje

    _MARRIAGE_ORDER_WORDS = {
        1: "први",
        2: "други",
        3: "трећи",
        4: "четврти",
        # Add more if needed
    }

    def handle(self, *args, **kwargs):
        self.clear_target_table()
        records = list(self._fetch_records())
        created_count = self._migrate_records(records)
        self.log_success(created_count, "венчања")
        self.drop_staging_table()

    def _fetch_records(self):
        with connection.cursor() as cursor:
            cursor.execute(f"""
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
                FROM {self.staging_table_name}
                ORDER BY "V_SIFRA"
            """)
            for row in cursor.fetchall():
                yield self._parse_record(row)

    def _parse_record(self, row) -> VencanjeRecord:
        def s(v):
            return Konvertor.string(v or "")

        def i(v, default=0):
            return Konvertor.int(v, default) if v is not None else default

        return VencanjeRecord(
            redni_broj=i(row[0], 0),
            godina=i(row[1], 1900),
            knjiga=s(row[2]),
            strana=s(row[3]),
            tekuci_broj=s(row[4]),
            datum=row[5],
            zenik_ime=s(row[6]),
            zenik_prezime=s(row[7]),
            zenik_zanimanje=s(row[8]),
            zenik_mesto=s(row[9]),
            zenik_veroispovest=s(row[10]),
            zenik_narodnost=s(row[11]),
            zenik_adresa=s(row[12]),
            nevesta_ime=s(row[13]),
            nevesta_prezime=s(row[14]),
            nevesta_zanimanje=s(row[15]),
            nevesta_mesto=s(row[16]),
            nevesta_veroispovest=s(row[17]),
            nevesta_narodnost=s(row[18]),
            nevesta_adresa=s(row[19]),
            svekar=s(row[20]),
            svekrva=s(row[21]),
            tast=s(row[22]),
            tasta=s(row[23]),
            zenik_god_rodj=i(row[24], 0),
            zenik_mes_rodj=i(row[25], 0),
            zenik_dan_rodj=i(row[26], 0),
            zenik_mesto_rodj=s(row[27]),
            nevesta_god_rodj=i(row[28], 0),
            nevesta_mes_rodj=i(row[29], 0),
            nevesta_dan_rodj=i(row[30], 0),
            nevesta_mesto_rodj=s(row[31]),
            zenik_rb_braka=i(row[32], 1),
            nevesta_rb_braka=i(row[33], 1),
            ispit_godina=i(row[34], 0),
            ispit_mesec=i(row[35], 0),
            ispit_dan=i(row[36], 0),
            hram_naziv=s(row[37]),
            svestenik_id=i(row[38], 0),
            kum_puno_ime=s(row[39]),
            stari_svat=s(row[40]),
            razresenje=s(row[41]),
            razresenje_txt=s(row[42]),
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

    def _build_vencanje_data(self, r: VencanjeRecord) -> Optional[dict]:
        # Validate required fields
        if not (
            r.zenik_ime.strip()
            and r.zenik_prezime.strip()
            and r.nevesta_ime.strip()
            and r.nevesta_prezime.strip()
        ):
            self.log_warning(
                f"Прескачем венчање без имена/презимена: "
                f"женик '{r.zenik_ime} {r.zenik_prezime}', "
                f"невеста '{r.nevesta_ime} {r.nevesta_prezime}'"
            )
            return None

        # Fix zero dates (0 → 1900-01-01)
        def fix_date(y, m, d):
            return (1900 if y == 0 else y, 1 if m == 0 else m, 1 if d == 0 else d)

        z_y, z_m, z_d = fix_date(r.zenik_god_rodj, r.zenik_mes_rodj, r.zenik_dan_rodj)
        n_y, n_m, n_d = fix_date(
            r.nevesta_god_rodj, r.nevesta_mes_rodj, r.nevesta_dan_rodj
        )
        i_y, i_m, i_d = fix_date(r.ispit_godina, r.ispit_mesec, r.ispit_dan)

        datum_rodj_zenik = date(z_y, z_m, z_d)
        datum_rodj_nevesta = date(n_y, n_m, n_d)
        datum_ispita = date(i_y, i_m, i_d)

        # Related models
        hram_clean = re.sub(r"(?i)\bhram\b", "", r.hram_naziv).strip()
        hram, _ = Hram.objects.get_or_create(naziv=Konvertor.string(hram_clean))

        svestenik, _ = Svestenik.objects.get_or_create(uid=r.svestenik_id)

        # Persons
        zenik = self._find_or_create_osoba(
            ime=r.zenik_ime.strip(),
            prezime=r.zenik_prezime.strip(),
            pol="М",
            datum_rodjenja=datum_rodj_zenik,
            mesto_rodjenja=r.zenik_mesto_rodj,
            zanimanje=r.zenik_zanimanje,
            veroispovest=r.zenik_veroispovest,
            narodnost=r.zenik_narodnost,
        )

        nevesta = self._find_or_create_osoba(
            ime=r.nevesta_ime.strip(),
            prezime=r.nevesta_prezime.strip(),
            pol="Ж",
            datum_rodjenja=datum_rodj_nevesta,
            mesto_rodjenja=r.nevesta_mesto_rodj,
            zanimanje=r.nevesta_zanimanje,
            veroispovest=r.nevesta_veroispovest,
            narodnost=r.nevesta_narodnost,
        )

        kum = None
        if cleaned_name := r.kum_puno_ime.strip():
            kum_ime, kum_prez = self._split_full_name(cleaned_name)
            if kum_ime and kum_prez:
                kum = self._find_or_create_osoba(ime=kum_ime, prezime=kum_prez)
            else:
                self.log_warning(f"Неуспело цепање имена кума: '{cleaned_name}'")

        return {
            "zenik": zenik,
            "nevesta": nevesta,
            "kum": kum,
            "hram": hram,
            "svestenik": svestenik,
            "redni_broj_vencanja_tekuca_godina": r.redni_broj,
            "vencanje_tekuca_godina": r.godina,
            "knjiga": Konvertor.int(r.knjiga, 0),
            "strana": Konvertor.int(r.strana, 0),
            "tekuci_broj": Konvertor.int(r.tekuci_broj, 0),
            "datum": r.datum,
            "mesto_zenika": r.zenik_mesto,
            "adresa_zenika": r.zenik_adresa,
            "mesto_neveste": r.nevesta_mesto,
            "adresa_neveste": r.nevesta_adresa,
            "svekar": r.svekar,
            "svekrva": r.svekrva,
            "tast": r.tast,
            "tasta": r.tasta,
            "zenik_rb_brak": self._marriage_order_word(r.zenik_rb_braka),
            "nevesta_rb_brak": self._marriage_order_word(r.nevesta_rb_braka),
            "datum_ispita": datum_ispita,
            "stari_svat": r.stari_svat,
            "razresenje": "нису" if r.razresenje.strip().upper() == "N" else "јесу",
            "razresenje_primedba": r.razresenje_txt,
            "primedba": "",
        }

    def _marriage_order_word(self, num: int) -> str:
        return self._MARRIAGE_ORDER_WORDS.get(num, "први")

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
