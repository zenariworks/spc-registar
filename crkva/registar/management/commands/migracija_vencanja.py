"""
Migracija tabele venčanja iz PostgreSQL staging tabele 'hsp_vencanja' u tabelu 'vencanja'
Poboljšana verzija: brža (bulk_create), robusnija, čišća.
"""

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.db import IntegrityError, connection
from django.db.transaction import atomic
from registar.management.commands.base_migration import MigrationCommand
from registar.management.commands.convert_utils import Konvertor
from registar.models import Hram, Osoba, Svestenik, Vencanje


@dataclass
class VencanjeRecord:
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
    zenik_adresa: str
    zenik_datum_rodj: Optional[date]
    zenik_mesto_rodj: str

    nevesta_ime: str
    nevesta_prezime: str
    nevesta_zanimanje: str
    nevesta_mesto: str
    nevesta_adresa: str
    nevesta_datum_rodj: Optional[date]
    nevesta_mesto_rodj: str

    svekar: str
    svekrva: str
    tast: str
    tasta: str

    zenik_rb_braka: int
    nevesta_rb_braka: int

    datum_ispita: Optional[date]

    hram_naziv: str
    svestenik_id: int

    kum_puno_ime: str
    stari_svat: str

    razresenje: str
    razresenje_txt: str


class Command(MigrationCommand):
    help = "Migracija tabele venčanja iz PostgreSQL staging tabele 'hsp_vencanja'"
    staging_table_name = "hsp_vencanja"
    target_model = Vencanje

    BATCH_SIZE = 500

    def handle(self, *args, **kwargs):
        self.clear_target_table()
        records = list(self._fetch_records())
        self.stdout.write(f"Учитано {len(records)} записа из staging табеле.")

        created_count = self._migrate_records(records)
        self.log_success(created_count, "венчања")
        self.drop_staging_table()

    def _fetch_records(self):
        columns = (
            "V_SIFRA",
            "V_AKTGOD",
            "V_KNJIGA",
            "V_STRANA",
            "V_TEKBROJ",
            "V_DATUM",
            "V_Z_IME",
            "V_Z_PREZ",
            "V_Z_ZANIM",
            "V_Z_MESTO",
            "V_Z_ADRESA",
            "V_Z_RODJG",
            "V_Z_RODJM",
            "V_Z_RODJD",
            "V_Z_RODJME",
            "V_N_IME",
            "V_N_PREZ",
            "V_N_ZANIM",
            "V_N_MESTO",
            "V_N_ADRESA",
            "V_N_RODJG",
            "V_N_RODJM",
            "V_N_RODJD",
            "V_N_RODJME",
            "V_ZR_OTAC",
            "V_ZR_MAJKA",
            "V_NR_OTAC",
            "V_NR_MAJKA",
            "V_Z_BRAK",
            "V_N_BRAK",
            "V_ISPITGOD",
            "V_ISPITMES",
            "V_ISPITDAN",
            "V_HRIME",
            "V_RBRSVEST",
            "V_KUM",
            "V_SSVAT",
            "V_RAZRDN",
            "V_RAZRTXT",
        )

        query = f"""
            SELECT {', '.join(f'"{col}"' for col in columns)}
            FROM {self.staging_table_name}
            ORDER BY "V_SIFRA"
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                yield self._parse_record(row)

    def _parse_record(self, row) -> VencanjeRecord:
        s = Konvertor.string

        def i(v, default=0):
            return Konvertor.int(v, default) if v is not None else default

        def _safe_date(y: int, m: int, d: int) -> Optional[date]:
            y = y or 1900
            m = m or 1
            d = d or 1
            if y < 1900:
                return None
            try:
                return date(y, m, d)
            except ValueError:
                return None

        return VencanjeRecord(
            redni_broj=i(row[0]),
            godina=i(row[1], 1900),
            knjiga=s(row[2]),
            strana=s(row[3]),
            tekuci_broj=s(row[4]),
            datum=row[5],
            zenik_ime=s(row[6]),
            zenik_prezime=s(row[7]),
            zenik_zanimanje=s(row[8]),
            zenik_mesto=s(row[9]),
            zenik_adresa=s(row[10]),
            zenik_datum_rodj=_safe_date(i(row[11]), i(row[12]), i(row[13])),
            zenik_mesto_rodj=s(row[14]),
            nevesta_ime=s(row[15]),
            nevesta_prezime=s(row[16]),
            nevesta_zanimanje=s(row[17]),
            nevesta_mesto=s(row[18]),
            nevesta_adresa=s(row[19]),
            nevesta_datum_rodj=_safe_date(i(row[20]), i(row[21]), i(row[22])),
            nevesta_mesto_rodj=s(row[23]),
            svekar=s(row[24]),
            svekrva=s(row[25]),
            tast=s(row[26]),
            tasta=s(row[27]),
            zenik_rb_braka=max(i(row[28]), 1),
            nevesta_rb_braka=max(i(row[29]), 1),
            datum_ispita=_safe_date(i(row[30]), i(row[31]), i(row[32])),
            hram_naziv=s(row[33]),
            svestenik_id=i(row[34]),
            kum_puno_ime=s(row[35]),
            stari_svat=s(row[36]),
            razresenje=s(row[37]),
            razresenje_txt=s(row[38]),
        )

    @atomic
    def _migrate_records(self, records):
        created_count = 0
        objekti = []

        # Predkeširaj objekte koji se često koriste
        svestenici = {s.uid: s for s in Svestenik.objects.all()}
        hramovi = {}

        for idx, record in enumerate(records, 1):
            try:
                data = self._build_vencanje_data(record, svestenici, hramovi)
                if data is None:
                    continue

                objekti.append(Vencanje(**data))
                created_count += 1

                if len(objekti) >= self.BATCH_SIZE:
                    Vencanje.objects.bulk_create(objekti, ignore_conflicts=False)
                    objekti.clear()
                    self.stdout.write(f"Обрађено {idx} записа...")

            except Exception as e:
                self.log_error(
                    f"Грешка на запису {record.redni_broj}/{record.godina}: {e}"
                )
                continue

        if objekti:
            try:
                Vencanje.objects.bulk_create(objekti)
            except IntegrityError as e:
                self.log_error(f"IntegrityError при bulk_create последњег batch-а: {e}")
                # Opcionalno: pojedinačno umetanje za debagovanje
                for objekat in objekti:
                    try:
                        objekat.save()
                    except Exception as ie:
                        self.log_error(f"Пропао појединачни save: {ie}")

        return created_count

    def _get_or_create_hram(self, naziv: str, cache: dict) -> Hram:
        if not naziv:
            naziv = "Непознат храм"
        else:
            naziv = re.sub(r"(?i)\bhram\b", "", naziv).strip()
            naziv = naziv or "Непознат храм"

        if naziv not in cache:
            hram, _ = Hram.objects.get_or_create(naziv=naziv)
            cache[naziv] = hram
        return cache[naziv]

    def _find_or_create_osoba(self, ime: str, prezime: str, **extra) -> Optional[Osoba]:
        if not ime or not prezime:
            return None

        ime = ime.strip()
        prezime = prezime.strip()
        if not ime or not prezime:
            return None

        osoba = Osoba.objects.filter(ime__iexact=ime, prezime__iexact=prezime).first()
        if osoba:
            # Ažuriraj samo prazna polja
            updates = {
                k: v for k, v in extra.items() if v and not getattr(osoba, k, None)
            }
            if updates:
                Osoba.objects.filter(pk=osoba.pk).update(**updates)
            return osoba

        create_data = {"ime": ime, "prezime": prezime, "parohijan": False}
        create_data.update({k: v for k, v in extra.items() if v is not None})
        return Osoba.objects.create(**create_data)

    def _clean_prezime(self, prezime: str) -> str:
        """Очисти презиме од префикса као што су 'р.', 'р ', 'r.', итд."""
        if not prezime:
            return prezime
        # Уклони префикс р. (рођена) са почетка презимена
        prezime = re.sub(r"^р\.?\s*", "", prezime, flags=re.IGNORECASE).strip()
        prezime = re.sub(r"^r\.?\s*", "", prezime, flags=re.IGNORECASE).strip()
        return prezime

    def _build_vencanje_data(
        self, r: VencanjeRecord, svestenici_cache: dict, hramovi_cache: dict
    ) -> Optional[dict]:
        zenik_ime = r.zenik_ime.strip()
        zenik_prezime = self._clean_prezime(r.zenik_prezime.strip())
        nevesta_ime = r.nevesta_ime.strip()
        nevesta_prezime = self._clean_prezime(r.nevesta_prezime.strip())

        if not (zenik_ime and zenik_prezime and nevesta_ime and nevesta_prezime):
            self.log_warning(
                f"Прескочено венчање {r.redni_broj}/{r.godina}: "
                f"непотпуна имена женика/невесте"
            )
            return None

        hram = self._get_or_create_hram(r.hram_naziv, hramovi_cache)
        svestenik = svestenici_cache.get(r.svestenik_id)

        zenik = self._find_or_create_osoba(
            ime=zenik_ime,
            prezime=zenik_prezime,
            pol="М",
            datum_rodjenja=r.zenik_datum_rodj,
            mesto_rodjenja=r.zenik_mesto_rodj or None,
            zanimanje=r.zenik_zanimanje or None,
        )

        nevesta = self._find_or_create_osoba(
            ime=nevesta_ime,
            prezime=zenik_prezime,
            pol="Ж",
            datum_rodjenja=r.nevesta_datum_rodj,
            mesto_rodjenja=r.nevesta_mesto_rodj or None,
            zanimanje=r.nevesta_zanimanje or None,
            devojacko_prezime=nevesta_prezime,
        )

        kum = None
        if kum_full := r.kum_puno_ime.strip():
            kum_ime, kum_prez = self.split_full_name(kum_full)
            if kum_ime and kum_prez:
                kum = self._find_or_create_osoba(ime=kum_ime, prezime=kum_prez)
            else:
                self.log_warning(
                    f"Неуспело цепање имена кума: '{kum_full}' (ред {r.redni_broj})"
                )

        # Roditelji
        svekar = self._parse_and_create_parent(r.svekar)
        svekrva = self._parse_and_create_parent(r.svekrva)
        tast = self._parse_and_create_parent(r.tast)
        tasta = self._parse_and_create_parent(r.tasta)

        # Stari svat
        stari_svat = None
        if ss_str := r.stari_svat.strip():
            ss_ime, ss_prez = self.split_full_name(ss_str.split(",")[0].strip())
            if ss_ime and ss_prez:
                stari_svat = self._find_or_create_osoba(ime=ss_ime, prezime=ss_prez)
            else:
                self.log_warning(f"Неуспело цепање старог свата: '{ss_str}'")

        return {
            "godina_registracije": r.godina if r.godina >= 1900 else 2000,
            "redni_broj": r.redni_broj,
            "knjiga": Konvertor.int(r.knjiga, 1),
            "strana": Konvertor.int(r.strana, 1),
            "tekuci_broj": Konvertor.int(r.tekuci_broj, 1),
            "datum": r.datum,
            "zenik": zenik,
            "nevesta": nevesta,
            "kum": kum,
            "mesto_zenika": r.zenik_mesto or "",
            "adresa_zenika": r.zenik_adresa or "",
            "mesto_neveste": r.nevesta_mesto or "",
            "adresa_neveste": r.nevesta_adresa or "",
            "zenik_rb_brak": r.zenik_rb_braka,
            "nevesta_rb_brak": r.nevesta_rb_braka,
            "svekar": svekar,
            "svekrva": svekrva,
            "tast": tast,
            "tasta": tasta,
            "stari_svat": stari_svat,
            "datum_ispita": r.datum_ispita,
            "hram": hram,
            "svestenik": svestenik,
            "razresenje": (r.razresenje or "").strip().upper() == "D",
            "primedba": (r.razresenje_txt or "").strip(),
        }

    def _parse_and_create_parent(self, full_str: str) -> Optional[Osoba]:
        if not full_str:
            return None
        name_part = full_str.split(",")[0].strip()
        ime, prezime = self.split_full_name(name_part)
        if ime and prezime:
            return self._find_or_create_osoba(ime=ime, prezime=prezime)
        return None
