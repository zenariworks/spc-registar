"""Миграција табеле крштења из staging табеле 'hsp_krstenja' у Krstenje.

Структура (иста као migracija_vencanja):
  1. SOURCE_COLUMNS
  2. KrstenjeRecord dataclass
  3. parse_row()
  4. Command (orchestration + transform)

Заједничка логика живи у пакету `registar.migracija`.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init,too-many-locals,broad-exception-caught,not-callable

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterator, Optional

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.transaction import atomic
from registar.management.commands.base_migration import MigrationCommand
from registar.migracija.address import find_or_create_adresa, set_adresa_if_empty
from registar.migracija.cache import (
    LookupCache,
    normalise_hram_naziv,
    normalise_zanimanje,
)
from registar.migracija.errors import RecordContext, RecordSkipped
from registar.migracija.helpers import (
    clean_prezime,
    cyr,
    cyr_int,
    extract_maiden,
    parse_time,
    split_full_name_last_word,
)
from registar.migracija.osoba_repo import find_or_create_osoba
from registar.migracija.sex import infer_sex_from_name
from registar.models import (
    Hram,
    Krstenje,
    Narodnost,
    Osoba,
    Svestenik,
    Veroispovest,
    Zanimanje,
)
from registar.utils_parser import parse_vera_narodnost

SOURCE_COLUMNS = (
    "K_SIFRA",
    "K_PROKNJ",
    "K_PROTBR",
    "K_PROTST",
    "K_AKTGOD",
    "K_IZ",
    "K_ULICA",
    "K_BROJ",
    "K_RODJGOD",
    "K_RODJMESE",
    "K_RODJDAN",
    "K_RODJVRE",
    "K_RODJMEST",
    "K_RODJOPST",
    "K_KRSGOD",
    "K_KRSMESE",
    "K_KRSDAN",
    "K_KRSVRE",
    "K_KRSMEST",
    "K_KRSHRAM",
    "K_DETIME",
    "K_DETIMEG",
    "K_DETPOL",
    "K_RODIME",
    "K_RODPREZ",
    "K_RODZANIM",
    "K_RODMEST",
    "K_RODVERA",
    "K_RODNAROD",
    "K_ROD2IME",
    "K_ROD2PREZ",
    "K_ROD2ZAN",
    "K_ROD2MEST",
    "K_ROD2VERA",
    "K_DETZIVO",
    "K_DETKOJE",
    "K_DETBRAC",
    "K_DETBLIZ",
    "K_DETBLIZ2",
    "K_DETMANA",
    "K_RBRSVE",
    "K_KUMIME",
    "K_KUMPREZ",
    "K_KUMZANIM",
    "K_KUMMEST",
    "K_REGMESTO",
    # K_REGKADA (датум регистрације) изостављен: DBF 'D' поље је празно
    # у целом извору (0/3579), па је селект био мртав уз тврдо
    # registracija_datum=None. Нема шта да се учита (#254).
    "K_REGBROJ",
    "K_REGSTR",
)


def _date_or_default(y: int, m: int, d: int) -> date:
    """Pre-1900 / zero values are coerced to 1900-01-01 (matches legacy behaviour)."""
    return date(1900 if y == 0 else y, 1 if m == 0 else m, 1 if d == 0 else d)


@dataclass
class KrstenjeRecord:  # pylint: disable=too-many-instance-attributes
    """One parsed staging row, fully transliterated."""

    redni_broj: int
    knjiga: str
    broj: str
    strana: int
    godina_registracije: int

    adresa_deteta_grad: str
    adresa_deteta_ulica: str
    adresa_deteta_broj: str

    datum_rodjenja: date
    rodjenje_vreme: str
    rodjenje_mesto: str
    rodjenje_opstina: str

    datum_krstenja: date
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

    zivorodjeno: str
    po_redu: int | None
    vanbracno: str
    blizanac: str
    blizanac_ime: str
    dete_sa_manom: str

    svestenik_id: int

    kum_puno_ime: str
    kum_prezime: str
    kum_zanimanje: str
    kum_mesto: str

    registracija_mesto: str
    registracija_broj: Optional[str]
    registracija_strana: Optional[str]

    @property
    def context(self) -> RecordContext:
        return RecordContext(
            table="hsp_krstenja",
            redni_broj=self.redni_broj,
            godina=self.godina_registracije,
            knjiga=self.knjiga,
            strana=str(self.strana),
            broj=self.broj,
        )


def parse_row(row: tuple) -> KrstenjeRecord:
    return KrstenjeRecord(
        redni_broj=cyr_int(row[0]),
        knjiga=cyr(row[1]),
        broj=cyr(row[2]),
        strana=cyr_int(row[3]),
        godina_registracije=cyr_int(row[4]),
        adresa_deteta_grad=cyr(row[5]),
        adresa_deteta_ulica=cyr(row[6]),
        adresa_deteta_broj=cyr(row[7]),
        datum_rodjenja=_date_or_default(
            cyr_int(row[8]), cyr_int(row[9]), cyr_int(row[10])
        ),
        rodjenje_vreme=cyr(row[11]),
        rodjenje_mesto=cyr(row[12]),
        rodjenje_opstina=cyr(row[13]),
        datum_krstenja=_date_or_default(
            cyr_int(row[14]), cyr_int(row[15]), cyr_int(row[16])
        ),
        krstenje_vreme=cyr(row[17]),
        krstenje_mesto=cyr(row[18]),
        hram_naziv=cyr(row[19]),
        dete_ime=cyr(row[20]),
        dete_gradjansko_ime=cyr(row[21]),
        dete_pol=cyr(row[22]),
        otac_ime=cyr(row[23]),
        otac_prezime=cyr(row[24]),
        otac_zanimanje=cyr(row[25]),
        otac_adresa=cyr(row[26]),
        otac_veroispovest=cyr(row[27]),
        otac_narodnost=cyr(row[28]),
        majka_ime=cyr(row[29]),
        majka_prezime=cyr(row[30]),
        majka_zanimanje=cyr(row[31]),
        majka_adresa=cyr(row[32]),
        majka_veroispovest=cyr(row[33]),
        zivorodjeno=cyr(row[34]),
        po_redu=cyr_int(row[35]) or None,
        vanbracno=cyr(row[36]),
        blizanac=cyr(row[37]),
        blizanac_ime=cyr(row[38]),
        dete_sa_manom=cyr(row[39]),
        svestenik_id=cyr_int(row[40]),
        kum_puno_ime=cyr(row[41]),
        kum_prezime=cyr(row[42]),
        kum_zanimanje=cyr(row[43]),
        kum_mesto=cyr(row[44]),
        registracija_mesto=cyr(row[45]),
        # K_REGKADA уклоњен из SOURCE_COLUMNS (#254) → K_REGBROJ/K_REGSTR
        # су се померили на индексе 46/47.
        registracija_broj=cyr(row[46]) or None,
        registracija_strana=cyr(row[47]) or None,
    )


class Command(MigrationCommand):
    help = "Миграција табеле крштења из staging табеле 'hsp_krstenja'"
    staging_table = "hsp_krstenja"
    target_model = Krstenje

    def handle(self, *args, **opts):
        self.zabrani_nad_public()
        self._verbose = opts.get("verbose_errors", False)
        self._dry_run = opts.get("dry_run", False)
        limit: int = opts.get("limit", 0) or 0

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

        records = list(self.take(self._fetch_records(), limit))
        self.stdout.write(
            f"Учитано {len(records)} записа из staging табеле"
            + (f" (--limit {limit})" if limit else "")
            + "."
        )

        created = self._build_and_save(records)
        self.log_success(created, "крштења")
        if self._dry_run:
            self.log_warning("DRY RUN — ништа није уписано у базу.")
        else:
            self.drop_staging_table()

    # ---------------- Pipeline ----------------

    def _fetch_records(self) -> Iterator[KrstenjeRecord]:
        col_list = ", ".join(f'"{c}"' for c in SOURCE_COLUMNS)
        query = f'SELECT {col_list} FROM {self.staging_table} ORDER BY "K_SIFRA"'
        with connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                yield parse_row(row)

    @atomic
    def _build_and_save(self, records: list[KrstenjeRecord]) -> int:
        # Clear inside the same transaction as the writes: if the import
        # aborts, the delete rolls back too and existing data survives (#329).
        if not self._dry_run:
            self.clear_target_table()
        created = 0
        dedup_skipped = 0
        # Source DBF (HSPKRST) contains true duplicates where the same baptism
        # was entered twice (same child name + baptism date + citation). We
        # dedupe on (god, knj, str, broj, dete_ime, dete_prezime, datum) so
        # legitimate twins (same citation, different child) and registry typos
        # (different prezime spelling) are preserved.
        seen: set[tuple] = set()
        for r in records:
            try:
                # Savepoint: a failed row rolls back alone instead of marking
                # the outer transaction rollback-only.
                with atomic():
                    data = self._build_krstenje(r)
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
            dete = data.get("dete")
            key = (
                data.get("godina_registracije"),
                data.get("knjiga"),
                data.get("strana"),
                data.get("broj"),
                (dete.ime.casefold() if dete and dete.ime else None),
                (dete.prezime.casefold() if dete and dete.prezime else None),
                data.get("datum"),
            )
            if key in seen:
                dedup_skipped += 1
                self.log_skip(r.context, "дупликат — иста citation + дете + датум")
                continue
            seen.add(key)
            if self._dry_run:
                created += 1
                continue
            try:
                with atomic():
                    Krstenje.objects.create(**data)
                created += 1
            except IntegrityError as e:
                self.log_error(r.context, f"IntegrityError: {e}")
        if dedup_skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"Прескочено као дупликати у извору: {dedup_skipped}"
                )
            )
        return created

    # ---------------- Transform ----------------

    def _build_krstenje(self, r: KrstenjeRecord) -> Optional[dict]:
        dete_ime = r.dete_ime.strip()
        otac_prezime = clean_prezime(r.otac_prezime.strip())
        if not dete_ime or not otac_prezime:
            raise RecordSkipped(r.context, "недостаје име детета или презиме оца")

        hram = self._hram.get(r.hram_naziv) or self._hram.get("Непознат храм")
        svestenik, _ = Svestenik.objects.get_or_create(uid=r.svestenik_id)

        otac_vera, otac_narod, majka_vera, majka_narod = self._parse_vera_narod_parents(
            r
        )

        dete = find_or_create_osoba(
            ime=dete_ime,
            prezime=otac_prezime,
            pol="М" if r.dete_pol.strip() == "1" else "Ж",
            datum_rodjenja=r.datum_rodjenja,
            vreme_rodjenja=parse_time(r.rodjenje_vreme),
            mesto_rodjenja=r.rodjenje_mesto,
        )

        otac = find_or_create_osoba(
            ime=r.otac_ime.strip(),
            prezime=otac_prezime,
            pol="М",
            zanimanje=self._zanimanje.get(r.otac_zanimanje),
            veroispovest=otac_vera,
            narodnost=otac_narod,
        )

        # The mother's surname field in DBF often carries a "р.<X>" maiden
        # marker. Split it: if a marker is present the married surname is
        # blank in the source, so fall back to the father's surname
        # (otac_prezime) as the most likely married name.
        majka_married, majka_maiden = extract_maiden(r.majka_prezime.strip())
        majka_prezime = majka_married or otac_prezime
        majka = find_or_create_osoba(
            ime=r.majka_ime.strip(),
            prezime=majka_prezime,
            pol="Ж",
            zanimanje=self._zanimanje.get(r.majka_zanimanje),
            veroispovest=majka_vera,
            narodnost=majka_narod,
            devojacko_prezime=majka_maiden or None,
        )

        kum = self._parse_kum(r)

        if dete and r.dete_gradjansko_ime.strip() and not dete.gradjansko_ime:
            Osoba.objects.filter(pk=dete.pk).update(
                gradjansko_ime=r.dete_gradjansko_ime.strip()
            )

        # Adrese
        if dete and (r.adresa_deteta_grad or r.adresa_deteta_ulica):
            set_adresa_if_empty(
                dete,
                find_or_create_adresa(
                    ulica=r.adresa_deteta_ulica or "",
                    broj=r.adresa_deteta_broj or "",
                    mesto=r.adresa_deteta_grad,
                ),
            )
        if otac and r.otac_adresa:
            set_adresa_if_empty(otac, find_or_create_adresa(mesto=r.otac_adresa))
        if majka and r.majka_adresa:
            set_adresa_if_empty(majka, find_or_create_adresa(mesto=r.majka_adresa))
        if kum and r.kum_mesto:
            set_adresa_if_empty(kum, find_or_create_adresa(mesto=r.kum_mesto))

        return {
            "dete": dete,
            "otac": otac,
            "majka": majka,
            "kum": kum,
            "hram": hram,
            "svestenik": svestenik,
            "redni_broj": r.redni_broj,
            "godina_registracije": r.godina_registracije or r.datum_krstenja.year,
            "knjiga": cyr_int(r.knjiga, 0),
            "broj": cyr_int(r.broj, 0),
            "strana": cyr_int(r.strana, 0),
            "datum": r.datum_krstenja,
            "vreme": parse_time(r.krstenje_vreme),
            "zivorodjeno": r.zivorodjeno.strip() == "1",
            "po_redu": r.po_redu,
            "vanbracno": r.vanbracno.strip() == "1",
            "blizanac": r.blizanac.strip() == "1",
            "ime_blizanca": r.blizanac_ime,
            "telesna_mana": r.dete_sa_manom.strip() == "1",
            "mesto_registracije": r.registracija_mesto,
            "maticni_broj": r.registracija_broj,
            "strana_registracije": r.registracija_strana,
            "primedba": "",
        }

    def _parse_vera_narod_parents(self, r: KrstenjeRecord):
        """K_RODVERA may carry both parents; K_ROD2VERA may override for majka."""
        otac_data, majka_from_otac = parse_vera_narodnost(r.otac_veroispovest)
        otac_vera = self._vera.get(otac_data["veroispovest"])
        otac_narod = self._narod.get(otac_data["narodnost"])

        if r.otac_narodnost and r.otac_narodnost.strip():
            narod_parsed, _ = parse_vera_narodnost(r.otac_narodnost)
            if narod_parsed["narodnost"]:
                otac_narod = self._narod.get(narod_parsed["narodnost"])

        if r.majka_veroispovest and r.majka_veroispovest.strip():
            majka_data, _ = parse_vera_narodnost(r.majka_veroispovest)
            majka_vera = self._vera.get(majka_data["veroispovest"])
            majka_narod = self._narod.get(majka_data["narodnost"])
        elif majka_from_otac:
            majka_vera = self._vera.get(majka_from_otac["veroispovest"])
            majka_narod = self._narod.get(majka_from_otac["narodnost"])
        else:
            majka_vera = otac_vera
            majka_narod = otac_narod

        return otac_vera, otac_narod, majka_vera, majka_narod

    def _parse_kum(self, r: KrstenjeRecord) -> Optional[Osoba]:
        kum_full = r.kum_puno_ime.strip()
        if not kum_full:
            return None
        kum_prez = r.kum_prezime.strip()
        if kum_prez:
            kum_ime = kum_full
        else:
            kum_ime, kum_prez = split_full_name_last_word(kum_full)
        if not (kum_ime and kum_prez):
            if self._verbose:
                self.log_warning(f"Неуспело цепање имена кума: '{kum_full}'")
            return None
        return find_or_create_osoba(
            ime=kum_ime,
            prezime=kum_prez,
            pol=infer_sex_from_name(kum_ime),
            zanimanje=self._zanimanje.get(r.kum_zanimanje),
        )
