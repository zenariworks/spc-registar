"""Миграција табеле крштења из staging табеле 'hsp_krstenja' у Krstenje.

Структура (иста као migracija_vencanja):
  1. SOURCE_COLUMNS
  2. KrstenjeRecord dataclass
  3. parse_row()
  4. Command (orchestration + transform)

Заједничка логика живи у пакету `registar.migracija`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterator

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.transaction import atomic
from registar.migracija.address import dodaj_adresu, nadji_dodaj_adresu
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
    parse_time,
    podeli_zadnju_rec,
)
from registar.migracija.osoba_repo import dodaj_novu_osobu, find_or_create_osoba
from registar.migracija.sex import pol_prema_imenu
from registar.models import (
    Hram,
    Krstenje,
    Narodnost,
    Osoba,
    Svestenik,
    Veroispovest,
    Zanimanje,
)
from registar.utils_parser import pars_vera_narodnost
from registar.uvoz.base_migration import MigrationCommand

SOURCE_COLUMNS = (
    "K_SIFRA",  # redni_broj
    "K_PROKNJ",  # knjiga
    "K_PROTBR",  # broj
    "K_PROTST",  # strana
    "K_AKTGOD",  # godina_registracije
    "K_IZ",  # adresa_deteta_grad
    "K_ULICA",  # adresa_deteta_ulica
    "K_BROJ",  # adresa_deteta_broj
    "K_RODJGOD",  # datum_rodjenja
    "K_RODJMESE",
    "K_RODJDAN",
    "K_RODJVRE",  # rodjenje_vreme
    "K_RODJMEST",  # rodjenje_mesto
    "K_RODJOPST",  # rodjenje_opstina
    "K_KRSGOD",  # datum_krstenja
    "K_KRSMESE",
    "K_KRSDAN",
    "K_KRSVRE",  # krstenje_vreme
    "K_KRSMEST",  # krstenje_mesto
    "K_KRSHRAM",  # hram_naziv
    "K_DETIME",  # dete_ime
    "K_DETIMEG",  # dete_gradjansko_ime
    "K_DETPOL",  # dete_pol
    "K_RODIME",  # otac_ime
    "K_RODPREZ",  # otac_prezime
    "K_RODZANIM",  # otac_zanimanje
    "K_RODMEST",  # otac_adresa
    "K_RODVERA",  # otac_veroispovest
    "K_RODNAROD",  # otac_narodnost
    "K_ROD2IME",  # majka_ime
    "K_ROD2PREZ",  # majka_prezime
    "K_ROD2ZAN",  # majka_zanimanje
    "K_ROD2MEST",  # majka_adresa
    "K_ROD2VERA",  # majka_veroispovest
    "K_DETZIVO",  # zivorodjeno
    "K_DETKOJE",  # po_redu
    "K_DETBRAC",  # vanbracno
    "K_DETBLIZ",  # blizanac
    "K_DETBLIZ2",  # blizanac_ime
    "K_DETMANA",  # dete_sa_manom
    "K_RBRSVE",  # svestenik_id
    "K_KUMIME",  # kum_puno_ime
    "K_KUMPREZ",  # kum_prezime
    "K_KUMZANIM",  # kum_zanimanje
    "K_KUMMEST",  # kum_mesto
    "K_REGMESTO",  # registracija_mesto
    "K_REGBROJ",  # registracija_broj
    "K_REGSTR",  # registracija_strana
)


def _date_or_default(y: int, m: int, d: int) -> date:
    """Convert possibly invalid pre-1900 / zero dates to 1900-01-01 (legacy behavior)."""
    return date(
        1900 if y == 0 else y,
        1 if m == 0 else m,
        1 if d == 0 else d,
    )


@dataclass(frozen=True, slots=True)
class KrstenjeZapis:
    """Parsed and cleaned row from the staging table."""

    redni_broj: int
    knjiga: str
    broj: str
    strana: int
    godina_registracije: int

    adresa_deteta_grad: str
    adresa_deteta_ulica: str
    adresa_deteta_broj: str

    rodjenje_datum: date
    rodjenje_vreme: str
    rodjenje_mesto: str
    rodjenje_opstina: str

    krstenje_datum: date
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
    adresa_majke: str
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
    registracija_broj: str | None
    registracija_strana: str | None

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


def parse_row(row: tuple) -> KrstenjeZapis:
    """Parse raw DB row into a clean, typed record."""
    return KrstenjeZapis(
        redni_broj=cirilica_int(row[0]),
        knjiga=cirilica(row[1]),
        broj=cirilica(row[2]),
        strana=cirilica_int(row[3]),
        godina_registracije=cirilica_int(row[4]),
        adresa_deteta_grad=cirilica(row[5]),
        adresa_deteta_ulica=cirilica(row[6]),
        adresa_deteta_broj=cirilica(row[7]),
        rodjenje_datum=_date_or_default(
            cirilica_int(row[8]), cirilica_int(row[9]), cirilica_int(row[10])
        ),
        rodjenje_vreme=cirilica(row[11]),
        rodjenje_mesto=cirilica(row[12]),
        rodjenje_opstina=cirilica(row[13]),
        krstenje_datum=_date_or_default(
            cirilica_int(row[14]), cirilica_int(row[15]), cirilica_int(row[16])
        ),
        krstenje_vreme=cirilica(row[17]),
        krstenje_mesto=cirilica(row[18]),
        hram_naziv=cirilica(row[19]),
        dete_ime=cirilica(row[20]),
        dete_gradjansko_ime=cirilica(row[21]),
        dete_pol=cirilica(row[22]),
        otac_ime=cirilica(row[23]),
        otac_prezime=cirilica(row[24]),
        otac_zanimanje=cirilica(row[25]),
        otac_adresa=cirilica(row[26]),
        otac_veroispovest=cirilica(row[27]),
        otac_narodnost=cirilica(row[28]),
        majka_ime=cirilica(row[29]),
        majka_prezime=cirilica(row[30]),
        majka_zanimanje=cirilica(row[31]),
        adresa_majke=cirilica(row[32]),
        majka_veroispovest=cirilica(row[33]),
        zivorodjeno=cirilica(row[34]),
        po_redu=cirilica_int(row[35]) or None,
        vanbracno=cirilica(row[36]),
        blizanac=cirilica(row[37]),
        blizanac_ime=cirilica(row[38]),
        dete_sa_manom=cirilica(row[39]),
        svestenik_id=cirilica_int(row[40]),
        kum_puno_ime=cirilica(row[41]),
        kum_prezime=cirilica(row[42]),
        kum_zanimanje=cirilica(row[43]),
        kum_mesto=cirilica(row[44]),
        registracija_mesto=cirilica(row[45]),
        registracija_broj=cirilica(row[46]) or None,
        registracija_strana=cirilica(row[47]) or None,
    )


class Command(MigrationCommand):
    help = "Миграција табеле крштења из staging табеле 'hsp_krstenja'"
    staging_table = "hsp_krstenja"
    target_model = Krstenje

    def handle(self, *args, **options):
        self.zabrani_nad_public()

        self._verbose = options.get("verbose_errors", False)
        self._dry_run = options.get("dry_run", False)
        limit: int = options.get("limit", 0) or 0

        self._init_lookups()
        records = list(self.take(self._fetch_records(), limit))

        self.stdout.write(
            f"Учитано {len(records)} записа из staging табеле"
            f"{f' (--limit {limit})' if limit else ''}."
        )

        created = self._build_and_save(records)
        self.log_success(created, "крштења")

        if self._dry_run:
            self.log_warning("DRY RUN — ништа није уписано у базу.")
        else:
            self.drop_staging_table()

    def _init_lookups(self) -> None:
        """Initialize all lookup caches."""
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

    def _fetch_records(self) -> Iterator[KrstenjeZapis]:
        """Stream records from the staging table."""
        columns = ", ".join(f'"{col}"' for col in SOURCE_COLUMNS)
        query = f'SELECT {columns} FROM {self.staging_table} ORDER BY "K_SIFRA"'

        with connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                yield parse_row(row)

    @atomic
    def _build_and_save(self, records: list[KrstenjeZapis]) -> int:
        if not self._dry_run:
            self.clear_target_table()

        created = 0
        dedup_skipped = 0
        seen: set[tuple] = set()

        for record in records:
            try:
                with atomic():
                    data = self._build_krstenje(record)
            except RecordSkipped as exc:
                self.log_skip(exc.ctx, exc.reason)
                continue
            except (ValueError, IntegrityError, ValidationError) as exc:
                self.log_error(record.context, str(exc))
                continue

            if data is None:
                continue

            if self._is_duplicate(seen, data, record):
                dedup_skipped += 1
                self.log_skip(record.context, "дупликат — иста citation + дете + датум")
                continue

            if self._dry_run:
                created += 1
                continue

            try:
                with atomic():
                    Krstenje.objects.create(**data)
                created += 1
            except IntegrityError as exc:
                self.log_error(record.context, f"IntegrityError: {exc}")

        if dedup_skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"Прескочено као дупликати у извору: {dedup_skipped}"
                )
            )

        return created

    def _is_duplicate(
        self, seen: set[tuple], data: dict, record: KrstenjeZapis
    ) -> bool:
        """Dedupe on (godina, knjiga, strana, broj, dete_ime, dete_prezime, datum)."""
        dete = data.get("dete")
        key = (
            data.get("godina_registracije"),
            data.get("knjiga"),
            data.get("strana"),
            data.get("broj"),
            dete.ime.casefold() if dete and dete.ime else None,
            dete.prezime.casefold() if dete and dete.prezime else None,
            data.get("datum"),
        )
        if key in seen:
            return True
        seen.add(key)
        return False

    # ---------------- Transform ----------------

    def _build_krstenje(self, r: KrstenjeZapis) -> dict | None:
        dete_ime = r.dete_ime.strip()
        otac_prezime = ocisti_prezime(r.otac_prezime.strip())

        if not dete_ime or not otac_prezime:
            raise RecordSkipped(r.context, "недостаје име детета или презиме оца")

        hram = self._hram.get(r.hram_naziv) or self._hram.get("Непознат храм")
        svestenik = None
        if r.svestenik_id:
            svestenik, _ = Svestenik.objects.get_or_create(uid=r.svestenik_id)

        otac_vera, otac_narod, majka_vera, majka_narod = self._parse_vera_narod_parents(
            r
        )

        dete = dodaj_novu_osobu(
            ime=dete_ime,
            prezime=otac_prezime,
            pol="М" if r.dete_pol.strip() == "1" else "Ж",
            datum_rodjenja=r.rodjenje_datum,
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

        # Mother's maiden name handling
        majka_married, majka_maiden = izdvoj_devojacko(r.majka_prezime.strip())
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

        kum = self._rasclani_kuma(r)

        # Update citizen name if present
        if dete and r.dete_gradjansko_ime.strip() and not dete.gradjansko_ime:
            Osoba.objects.filter(pk=dete.pk).update(
                gradjansko_ime=r.dete_gradjansko_ime.strip()
            )

        self._set_addresses(dete, otac, majka, kum, r)

        return {
            "dete": dete,
            "otac": otac,
            "majka": majka,
            "kum": kum,
            "hram": hram,
            "svestenik": svestenik,
            "redni_broj": r.redni_broj,
            "godina_registracije": r.godina_registracije or r.krstenje_datum.year,
            "knjiga": cirilica_int(r.knjiga, 0),
            "broj": cirilica_int(r.broj, 0),
            "strana": cirilica_int(r.strana, 0),
            "datum": r.krstenje_datum,
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

    def _parse_vera_narod_parents(self, r: KrstenjeZapis):
        """Parse confession/nationality for both parents."""
        otac_data, majka_from_otac = pars_vera_narodnost(r.otac_veroispovest)
        otac_vera = self._vera.get(otac_data["veroispovest"])
        otac_narod = self._narod.get(otac_data["narodnost"])

        # Override with dedicated narodnost column if present
        if r.otac_narodnost and r.otac_narodnost.strip():
            narod_parsed, _ = pars_vera_narodnost(r.otac_narodnost)
            if narod_parsed["narodnost"]:
                otac_narod = self._narod.get(narod_parsed["narodnost"])

        # Mother
        if r.majka_veroispovest and r.majka_veroispovest.strip():
            majka_data, _ = pars_vera_narodnost(r.majka_veroispovest)
            majka_vera = self._vera.get(majka_data["veroispovest"])
            majka_narod = self._narod.get(majka_data["narodnost"])
        elif majka_from_otac:
            majka_vera = self._vera.get(majka_from_otac["veroispovest"])
            majka_narod = self._narod.get(majka_from_otac["narodnost"])
        else:
            majka_vera = otac_vera
            majka_narod = otac_narod

        return otac_vera, otac_narod, majka_vera, majka_narod

    def _rasclani_kuma(self, zapis: KrstenjeZapis) -> Osoba | None:
        """Parse and create godparent (kum)."""
        puno_ime = zapis.kum_puno_ime.strip()
        if not puno_ime:
            return None

        prezime = zapis.kum_prezime.strip()
        ime, prezime = (puno_ime, prezime) if prezime else podeli_zadnju_rec(puno_ime)

        if not (ime and prezime):
            if self._verbose:
                self.log_warning(f"Неуспело цепање имена кума: '{puno_ime}'")
            return None

        kumu_vencano, kumu_devojacko = izdvoj_devojacko(prezime)
        return find_or_create_osoba(
            ime=ime,
            prezime=kumu_vencano or kumu_devojacko,
            pol=pol_prema_imenu(ime),
            zanimanje=self._zanimanje.get(zapis.kum_zanimanje),
            devojacko_prezime=kumu_devojacko or None,
        )

    def _set_addresses(
        self,
        dete: Osoba,
        otac: Osoba,
        majka: Osoba,
        kum: Osoba | None,
        r: KrstenjeZapis,
    ) -> None:
        """Set addresses where available."""
        if dete and (r.adresa_deteta_grad or r.adresa_deteta_ulica):
            dodaj_adresu(
                dete,
                nadji_dodaj_adresu(
                    ulica=r.adresa_deteta_ulica or "",
                    broj=r.adresa_deteta_broj or "",
                    mesto=r.adresa_deteta_grad,
                ),
            )

        if otac and r.otac_adresa:
            dodaj_adresu(otac, nadji_dodaj_adresu(mesto=r.otac_adresa))

        if majka and r.adresa_majke:
            dodaj_adresu(majka, nadji_dodaj_adresu(mesto=r.adresa_majke))

        if kum and r.kum_mesto:
            dodaj_adresu(kum, nadji_dodaj_adresu(mesto=r.kum_mesto))
