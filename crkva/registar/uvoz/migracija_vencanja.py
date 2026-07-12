"""Миграција табеле венчања из staging табеле 'hsp_vencanja' у Vencanje.

Структура фајла:
  1. SOURCE_COLUMNS  — колоне из staging табеле, по реду
  2. VencanjeRecord  — dataclass који представља један парсиран ред
  3. parse_row()     — претвара ред (tuple) у VencanjeRecord
  4. build_vencanje_data() — претвара VencanjeRecord у kwargs за Vencanje()
  5. Command         — оркестрација: fetch → transform → batch insert

Заједничка логика (ocisti_prezime, nadji_dodaj_osobu, get/cache за
Veroispovest/Narodnost/Zanimanje/Hram, split_adresa) живи у пакету
`registar.migracija`.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init,too-many-locals,broad-exception-caught,not-callable

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterator

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.transaction import atomic
from registar.migracija.address import dodaj_adresu, rasclani_adresu
from registar.migracija.cache import (
    LookupCache,
    normalise_hram_naziv,
    normalise_zanimanje,
)
from registar.migracija.errors import RecordContext, RecordSkipped
from registar.migracija.helpers import (
    cirilica,
    cirilica_int,
    izdvoj_devojacko,
    ocisti_prezime,
    rasclani_puno_ime,
    safe_date,
)
from registar.migracija.osoba_repo import dodaj_osobu, nadji_dodaj_osobu
from registar.migracija.sex import pol_prema_imenu
from registar.models import (
    Hram,
    Narodnost,
    Osoba,
    Svestenik,
    Vencanje,
    Veroispovest,
    Zanimanje,
)
from registar.utils_parser import pars_vera_narodnost
from registar.uvoz.base_migration import MigrationCommand

SOURCE_COLUMNS = (
    "V_SIFRA",
    "V_AKTGOD",
    "V_KNJIGA",
    "V_STRANA",
    "V_TEKBROJ",
    "V_DATUM",
    "V_GODINA",
    "V_MESEC",
    "V_DAN",
    "V_Z_IME",
    "V_Z_PREZ",
    "V_Z_ZANIM",
    "V_Z_MESTO",
    "V_Z_ADRESA",
    "V_Z_VEROIS",
    "V_Z_NARODN",
    "V_Z_RODJG",
    "V_Z_RODJM",
    "V_Z_RODJD",
    "V_Z_RODJME",
    "V_N_IME",
    "V_N_PREZ",
    "V_N_ZANIM",
    "V_N_MESTO",
    "V_N_ADRESA",
    "V_N_VEROIS",
    "V_N_NARODN",
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
    "V_HRMESTO",
    "V_RBRSVEST",
    "V_KUM",
    "V_SSVAT",
    "V_RAZRDN",
    "V_RAZRTXT",
)


@dataclass
class VencanjeRecord:  # pylint: disable=too-many-instance-attributes
    """One parsed staging row, fully transliterated and date-typed."""

    redni_broj: int
    godina: int
    knjiga: str
    strana: str
    broj: str
    datum: date | None

    zenik_ime: str
    zenik_prezime: str
    zenik_zanimanje: str
    zenik_mesto: str
    zenik_adresa: str
    zenik_veroispovest: str
    zenik_narodnost: str
    zenik_datum_rodj: date | None
    zenik_mesto_rodj: str

    nevesta_ime: str
    nevesta_prezime: str
    nevesta_zanimanje: str
    nevesta_mesto: str
    nevesta_adresa: str
    nevesta_veroispovest: str
    nevesta_narodnost: str
    nevesta_datum_rodj: date | None
    nevesta_mesto_rodj: str

    svekar: str
    svekrva: str
    tast: str
    tasta: str

    zenik_rb_braka: int
    nevesta_rb_braka: int

    datum_ispita: date | None

    hram_naziv: str
    hram_mesto: str
    svestenik_id: int

    kum_puno_ime: str
    stari_svat_ime: str

    razresenje: str
    primedba: str

    @property
    def context(self) -> RecordContext:
        return RecordContext(
            table="hsp_vencanja",
            redni_broj=self.redni_broj,
            godina=self.godina,
            knjiga=self.knjiga,
            strana=self.strana,
            broj=self.broj,
        )


def parse_row(row: tuple) -> VencanjeRecord:
    """Tuple from cursor.fetchall() → VencanjeRecord. Pure, no DB access."""
    return VencanjeRecord(
        redni_broj=cirilica_int(row[0]),
        godina=cirilica_int(row[1], 1900),
        knjiga=cirilica(row[2]),
        strana=cirilica(row[3]),
        broj=cirilica(row[4]),
        datum=safe_date(
            cirilica_int(row[6]), cirilica_int(row[7]), cirilica_int(row[8])
        ),
        zenik_ime=cirilica(row[9]),
        zenik_prezime=cirilica(row[10]),
        zenik_zanimanje=cirilica(row[11]),
        zenik_mesto=cirilica(row[12]),
        zenik_adresa=cirilica(row[13]),
        zenik_veroispovest=cirilica(row[14]),
        zenik_narodnost=cirilica(row[15]),
        zenik_datum_rodj=safe_date(
            cirilica_int(row[16]), cirilica_int(row[17]), cirilica_int(row[18])
        ),
        zenik_mesto_rodj=cirilica(row[19]),
        nevesta_ime=cirilica(row[20]),
        nevesta_prezime=cirilica(row[21]),
        nevesta_zanimanje=cirilica(row[22]),
        nevesta_mesto=cirilica(row[23]),
        nevesta_adresa=cirilica(row[24]),
        nevesta_veroispovest=cirilica(row[25]),
        nevesta_narodnost=cirilica(row[26]),
        nevesta_datum_rodj=safe_date(
            cirilica_int(row[27]), cirilica_int(row[28]), cirilica_int(row[29])
        ),
        nevesta_mesto_rodj=cirilica(row[30]),
        svekar=cirilica(row[31]),
        svekrva=cirilica(row[32]),
        tast=cirilica(row[33]),
        tasta=cirilica(row[34]),
        zenik_rb_braka=max(cirilica_int(row[35]), 1),
        nevesta_rb_braka=max(cirilica_int(row[36]), 1),
        datum_ispita=safe_date(
            cirilica_int(row[37]), cirilica_int(row[38]), cirilica_int(row[39])
        ),
        hram_naziv=cirilica(row[40]),
        hram_mesto=cirilica(row[41]),
        svestenik_id=cirilica_int(row[42]),
        kum_puno_ime=cirilica(row[43]),
        stari_svat_ime=cirilica(row[44]),
        razresenje=cirilica(row[45]),
        primedba=cirilica(row[46]),
    )


class Command(MigrationCommand):
    help = "Миграција табеле венчања из staging табеле 'hsp_vencanja'"
    staging_table = "hsp_vencanja"
    target_model = Vencanje

    BATCH_SIZE = 500

    def handle(self, *args, **opts):
        self.zabrani_nad_public()
        self._verbose = opts.get("verbose_errors", False)
        self._dry_run = opts.get("dry_run", False)
        limit: int = opts.get("limit", 0) or 0

        # Caches
        self._vera = LookupCache(Veroispovest, "naziv")
        self._narod = LookupCache(Narodnost, "naziv")
        self._zanimanje = LookupCache(
            Zanimanje,
            "naziv",
            key_normaliser=normalise_zanimanje,
            extra_defaults={"sifra": ""},
        )
        self._hram = LookupCache(Hram, "naziv", key_normaliser=normalise_hram_naziv)
        self._vera.warm()
        self._narod.warm()
        self._svestenici = {s.uid: s for s in Svestenik.objects.all()}

        records = list(self.take(self._fetch_records(), limit))
        self.stdout.write(
            f"Учитано {len(records)} записа из staging табеле"
            + (f" (--limit {limit})" if limit else "")
            + "."
        )

        created = self._build_and_save(records)
        self.log_success(created, "венчања")
        if self._dry_run:
            self.log_warning("DRY RUN — ништа није уписано у базу.")
        else:
            self.drop_staging_table()

    # ---------------- Pipeline ----------------

    def _fetch_records(self) -> Iterator[VencanjeRecord]:
        col_list = ", ".join(f'"{c}"' for c in SOURCE_COLUMNS)
        query = f'SELECT {col_list} FROM {self.staging_table} ORDER BY "V_SIFRA"'
        with connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                yield parse_row(row)

    @atomic
    def _build_and_save(self, records: list[VencanjeRecord]) -> int:
        # Clear inside the same transaction as the writes: if the import
        # aborts, the delete rolls back too and existing data survives (#329).
        if not self._dry_run:
            self.clear_target_table()
        objects: list[Vencanje] = []
        created = 0

        for idx, r in enumerate(records, 1):
            try:
                # Savepoint: a failed row rolls back alone instead of marking
                # the outer transaction rollback-only.
                with atomic():
                    data = self._build_vencanje_data(r)
            except RecordSkipped as skip:
                self.log_skip(skip.ctx, skip.reason)
                continue
            except (ValueError, IntegrityError, ValidationError) as e:
                # Narrow except so OperationalError / ProgrammingError / KeyboardInterrupt
                # propagate and abort the run instead of being silently logged.
                self.log_error(r.context, str(e))
                continue

            if data is None:
                continue
            objects.append(Vencanje(**data))
            created += 1

            if len(objects) >= self.BATCH_SIZE:
                self._flush(objects)
                objects.clear()
                self.stdout.write(f"Обрађено {idx} записа...")

        if objects:
            self._flush(objects)
        return created

    def _flush(self, objects: list[Vencanje]) -> None:
        if self._dry_run:
            return
        try:
            with atomic():
                Vencanje.objects.bulk_create(objects, ignore_conflicts=False)
        except IntegrityError as e:
            self.log_error(f"bulk_create failed: {e}; retrying individually")
            for o in objects:
                try:
                    with atomic():
                        o.save()
                except (ValueError, IntegrityError, ValidationError) as ie:
                    self.log_error(f"individual save failed: {ie}")

    # ---------------- Transform ----------------

    def _build_vencanje_data(self, r: VencanjeRecord) -> dict | None:
        zenik_ime = r.zenik_ime.strip()
        zenik_prezime = ocisti_prezime(r.zenik_prezime.strip())
        nevesta_ime = r.nevesta_ime.strip()
        nevesta_prezime = ocisti_prezime(r.nevesta_prezime.strip())

        if not (zenik_ime and zenik_prezime and nevesta_ime and nevesta_prezime):
            raise RecordSkipped(r.context, "непотпуна имена женика/невесте")

        hram = self._hram.get(r.hram_naziv) or self._hram.get("Непознат храм")
        svestenik = self._svestenici.get(r.svestenik_id)

        zenik_vera, zenik_narod = self._parse_vera_narod(
            r.zenik_veroispovest, r.zenik_narodnost
        )
        nevesta_vera, nevesta_narod = self._parse_vera_narod(
            r.nevesta_veroispovest, r.nevesta_narodnost
        )

        # Женик и невеста су регистарски принципи — увек нове особе (#332).
        # Невеста се раније дедуплицирала под МЛАДОЖЕЊИНИМ презименом, па се
        # спајала са његовом мајком (свекрвом) истог имена; сада се увек
        # креира нова особа (удато презиме = зеник_презиме, девојачко =
        # nevesta_prezime).
        zenik = dodaj_osobu(
            ime=zenik_ime,
            prezime=zenik_prezime,
            pol="М",
            datum_rodjenja=r.zenik_datum_rodj,
            mesto_rodjenja=r.zenik_mesto_rodj or None,
            zanimanje=self._zanimanje.get(r.zenik_zanimanje),
            veroispovest=zenik_vera,
            narodnost=zenik_narod,
        )

        nevesta = dodaj_osobu(
            ime=nevesta_ime,
            prezime=zenik_prezime,  # married surname
            pol="Ж",
            datum_rodjenja=r.nevesta_datum_rodj,
            mesto_rodjenja=r.nevesta_mesto_rodj or None,
            zanimanje=self._zanimanje.get(r.nevesta_zanimanje),
            devojacko_prezime=nevesta_prezime,
            veroispovest=nevesta_vera,
            narodnost=nevesta_narod,
        )

        kum = self._rasclani_osobu(r.kum_puno_ime, label="кум")
        svekar = self._rasclani_roditelja(r.svekar, pol="М")
        svekrva = self._rasclani_roditelja(r.svekrva, pol="Ж")
        tast = self._rasclani_roditelja(r.tast, pol="М")
        tasta = self._rasclani_roditelja(r.tasta, pol="Ж")
        stari_svat = self._rasclani_osobu(
            r.stari_svat_ime.split(",")[0] if r.stari_svat_ime else "",
            label="стари сват",
        )

        # Addresses (only attach if Osoba doesn't already have one)
        if zenik and (r.zenik_adresa or r.zenik_mesto):
            dodaj_adresu(zenik, rasclani_adresu(r.zenik_adresa, r.zenik_mesto))
        if nevesta and (r.nevesta_adresa or r.nevesta_mesto):
            dodaj_adresu(nevesta, rasclani_adresu(r.nevesta_adresa, r.nevesta_mesto))

        return {
            "godina_registracije": r.godina if r.godina >= 1900 else 2000,
            "redni_broj": r.redni_broj,
            "knjiga": cirilica_int(r.knjiga, 1),
            "strana": cirilica_int(r.strana, 1),
            "broj": cirilica_int(r.broj, 1),
            "datum": r.datum,
            "zenik": zenik,
            "nevesta": nevesta,
            "kum": kum,
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
            "primedba": (r.primedba or "").strip(),
        }

    # ---------------- Person sub-parsing ----------------

    def _parse_vera_narod(self, vera_text: str, narod_text: str):
        """Parse blended vera/narodnost text (one column may contain both)."""
        vera_obj = None
        narod_obj = None
        if vera_text and vera_text.strip():
            parsed, _ = pars_vera_narodnost(vera_text)
            vera_obj = self._vera.get(parsed["veroispovest"])
            if not (narod_text and narod_text.strip()):
                narod_obj = self._narod.get(parsed["narodnost"])
        if narod_text and narod_text.strip():
            narod_parsed, _ = pars_vera_narodnost(narod_text)
            if narod_parsed["narodnost"]:
                narod_obj = self._narod.get(narod_parsed["narodnost"])
        return vera_obj, narod_obj

    def _rasclani_osobu(self, full_str: str, *, label: str) -> Osoba | None:
        if not full_str or not full_str.strip():
            return None
        ime, prezime = rasclani_puno_ime(full_str.split(",")[0].strip())
        if ime and prezime:
            married, maiden = izdvoj_devojacko(prezime)
            return nadji_dodaj_osobu(
                ime=ime,
                prezime=married or maiden,
                pol=pol_prema_imenu(ime),
                devojacko_prezime=maiden or None,
            )
        if self._verbose:
            self.log_warning(f"Неуспело цепање имена ({label}): '{full_str}'")
        return None

    def _rasclani_roditelja(
        self, full_str: str, pol: str | None = None
    ) -> Osoba | None:
        if not full_str:
            return None
        ime, prezime = rasclani_puno_ime(full_str.split(",")[0].strip())
        if ime and prezime:
            married, maiden = izdvoj_devojacko(prezime)
            return nadji_dodaj_osobu(
                ime=ime,
                prezime=married or maiden,
                pol=pol,
                devojacko_prezime=maiden or None,
            )
        return None
