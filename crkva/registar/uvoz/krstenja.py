"""Миграција табеле крштења из staging табеле 'hsp_krstenja' у Krstenje.

Структура (иста као migracija_vencanja):
  1. SOURCE_COLUMNS
  2. KrstenjeZapis dataclass
  3. parse_row()
  4. Command (оркестрација + претварање)

Заједничка логика живи у пакету `registar.utils.migracija`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterator

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.transaction import atomic
from registar.models import (
    Hram,
    Krstenje,
    Narodnost,
    Osoba,
    Svestenik,
    Veroispovest,
    Zanimanje,
)
from registar.utils.migracija.address import dodaj_adresu, nadji_dodaj_adresu
from registar.utils.migracija.cache import (
    LookupCache,
    normalizuj_naziv_hrama,
    normalizuj_zanimanje,
)
from registar.utils.migracija.errors import RecordContext, RecordSkipped
from registar.utils.migracija.helpers import (
    cirilica,
    cirilica_int,
    izdvoj_devojacko,
    ocisti_prezime,
    podeli_zadnju_rec,
    rasclani_vreme,
)
from registar.utils.migracija.osoba_repo import dodaj_osobu, nadji_dodaj_osobu
from registar.utils.migracija.pol import pol_prema_imenu
from registar.utils.parser import rasclani_vera_narodnost
from registar.uvoz.osnovno import MigrationCommand

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
    "K_REGBROJ",
    "K_REGSTR",
)
"""Колоне staging табеле, редом којим их чита ``parse_row``.

Значење сваке колоне види се из поља ``KrstenjeZapis`` у које ``parse_row``
пресипа исти индекс (нпр. ``K_PROKNJ`` → ``knjiga``, ``K_RBRSVE`` →
``svestenik_id``); тројке ``*GOD``/``*MESE``/``*DAN`` су датуми.
"""


def _date_or_default(y: int, m: int, d: int) -> date:
    """Датум у коме се нулти делови замењују са 1900 / 1 / 1 (старо понашање)."""
    return date(
        1900 if y == 0 else y,
        1 if m == 0 else m,
        1 if d == 0 else d,
    )


def _datum(row: tuple, i: int) -> date:
    """Датум из три узастопне колоне (година, месец, дан) почев од `row[i]`."""
    return _date_or_default(
        cirilica_int(row[i]), cirilica_int(row[i + 1]), cirilica_int(row[i + 2])
    )


@dataclass(frozen=True, slots=True)
class KrstenjeZapis:
    """Парсиран и очишћен ред из staging табеле."""

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
    majka_adresa: str
    majka_veroispovest: str

    zivorodjeno: str
    po_redu: int | None
    vanbracno: str
    blizanac: str
    blizanac_ime: str
    dete_sa_manom: str

    svestenik_id: int

    kum_ime: str
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
    """Сиров ред из базе → очишћен, типизован запис."""
    return KrstenjeZapis(
        redni_broj=cirilica_int(row[0]),
        knjiga=cirilica(row[1]),
        broj=cirilica(row[2]),
        strana=cirilica_int(row[3]),
        godina_registracije=cirilica_int(row[4]),
        adresa_deteta_grad=cirilica(row[5]),
        adresa_deteta_ulica=cirilica(row[6]),
        adresa_deteta_broj=cirilica(row[7]),
        rodjenje_datum=_datum(row, 8),
        rodjenje_vreme=cirilica(row[11]),
        rodjenje_mesto=cirilica(row[12]),
        rodjenje_opstina=cirilica(row[13]),
        krstenje_datum=_datum(row, 14),
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
        majka_adresa=cirilica(row[32]),
        majka_veroispovest=cirilica(row[33]),
        zivorodjeno=cirilica(row[34]),
        po_redu=cirilica_int(row[35]) or None,
        vanbracno=cirilica(row[36]),
        blizanac=cirilica(row[37]),
        blizanac_ime=cirilica(row[38]),
        dete_sa_manom=cirilica(row[39]),
        svestenik_id=cirilica_int(row[40]),
        kum_ime=cirilica(row[41]),
        kum_prezime=cirilica(row[42]),
        kum_zanimanje=cirilica(row[43]),
        kum_mesto=cirilica(row[44]),
        registracija_mesto=cirilica(row[45]),
        registracija_broj=cirilica(row[46]) or None,
        registracija_strana=cirilica(row[47]) or None,
    )


def _obavezna_imena(r: KrstenjeZapis) -> tuple[str, str]:
    """Име детета и очишћено презиме оца; без иједног ред се прескаче."""
    dete_ime = r.dete_ime.strip()
    otac_prezime = ocisti_prezime(r.otac_prezime.strip())
    if not dete_ime or not otac_prezime:
        raise RecordSkipped(r.context, "недостаје име детета или презиме оца")
    return dete_ime, otac_prezime


def _da(vrednost: str) -> bool:
    """Заставица из старе базе: "1" значи да."""
    return vrednost.strip() == "1"


def _podaci_zapisa(r: KrstenjeZapis) -> dict:
    """Поља крштења која се преузимају из реда без приступа бази."""
    return {
        "redni_broj": r.redni_broj,
        "godina_registracije": r.godina_registracije or r.krstenje_datum.year,
        "knjiga": cirilica_int(r.knjiga, 0),
        "broj": cirilica_int(r.broj, 0),
        "strana": cirilica_int(r.strana, 0),
        "datum": r.krstenje_datum,
        "vreme": rasclani_vreme(r.krstenje_vreme),
        "zivorodjeno": _da(r.zivorodjeno),
        "po_redu": r.po_redu,
        "vanbracno": _da(r.vanbracno),
        "blizanac": _da(r.blizanac),
        "ime_blizanca": r.blizanac_ime,
        "telesna_mana": _da(r.dete_sa_manom),
        "mesto_registracije": r.registracija_mesto,
        "maticni_broj": r.registracija_broj,
        "strana_registracije": r.registracija_strana,
        "primedba": "",
    }


def _dodaj_adresu_deteta(dete: Osoba, r: KrstenjeZapis) -> None:
    """Адреса детета (место, улица и број), ако је има у реду."""
    if dete and (r.adresa_deteta_grad or r.adresa_deteta_ulica):
        dodaj_adresu(
            dete,
            nadji_dodaj_adresu(
                ulica=r.adresa_deteta_ulica or "",
                broj=r.adresa_deteta_broj or "",
                mesto=r.adresa_deteta_grad,
            ),
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
        """Кешеви шифарника и свештеника за цео увоз."""
        self._vera = LookupCache(Veroispovest, "naziv")
        self._narod = LookupCache(Narodnost, "naziv")
        self._zanimanje = LookupCache(
            Zanimanje,
            "naziv",
            key_normaliser=normalizuj_zanimanje,
            extra_defaults={"sifra": ""},
        )
        self._hram = LookupCache(Hram, "naziv", key_normaliser=normalizuj_naziv_hrama)

        self._vera.warm()
        self._narod.warm()
        self._svestenici = {s.uid: s for s in Svestenik.objects.all()}

    def _fetch_records(self) -> Iterator[KrstenjeZapis]:
        """Чита записе из staging табеле."""
        columns = ", ".join(f'"{col}"' for col in SOURCE_COLUMNS)
        # S608: Табела и колоне су константе модула (staging_table, SOURCE_COLUMNS), не улаз корисника.
        query = f'SELECT {columns} FROM {self.staging_table} ORDER BY "K_SIFRA"'  # noqa: S608

        with connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                yield parse_row(row)

    @atomic
    def _build_and_save(self, records: list[KrstenjeZapis]) -> int:
        """Гради и уписује крштења у једној трансакцији; враћа број уписаних.

        Брисање циљне табеле је у истој трансакцији као упис, па неуспео увоз
        враћа и брисање. Дупликати из извора се прескачу и пребројавају.
        """
        if not self._dry_run:
            self.clear_target_table()

        created = 0
        dedup_skipped = 0
        seen: set[tuple] = set()

        for record in records:
            data = self._build_or_log(record)
            if data is None:
                continue
            if self._is_duplicate(seen, data, record):
                dedup_skipped += 1
                self.log_skip(record.context, "дупликат — иста citation + дете + датум")
                continue
            if self._sacuvaj(data, record):
                created += 1

        self._prijavi_duplikate(dedup_skipped)
        return created

    def _build_or_log(self, record: KrstenjeZapis) -> dict | None:
        """Подаци за једно крштење, или None ако је ред прескочен или неисправан.

        Сваки ред има свој savepoint, па неуспео ред враћа само себе. Хватају се
        само грешке података; остале прекидају увоз.
        """
        try:
            with atomic():
                return self._build_krstenje(record)
        except RecordSkipped as exc:
            self.log_skip(exc.ctx, exc.reason)
        except (ValueError, IntegrityError, ValidationError) as exc:
            self.log_error(record.context, str(exc))
        return None

    def _sacuvaj(self, data: dict, record: KrstenjeZapis) -> bool:
        """Уписује једно крштење у свом savepoint-у; уз --dry-run само броји."""
        if self._dry_run:
            return True
        try:
            with atomic():
                Krstenje.objects.create(**data)
        except IntegrityError as exc:
            self.log_error(record.context, f"IntegrityError: {exc}")
            return False
        return True

    def _prijavi_duplikate(self, broj: int) -> None:
        """Упозорење са бројем дупликата из извора, ако их је било."""
        if broj:
            self.stdout.write(
                self.style.WARNING(f"Прескочено као дупликати у извору: {broj}")
            )

    def _is_duplicate(
        self, seen: set[tuple], data: dict, record: KrstenjeZapis
    ) -> bool:
        """Дупликат по (година, књига, страна, број, име и презиме детета, датум)."""
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

    def _build_krstenje(self, r: KrstenjeZapis) -> dict | None:
        """Kwargs за Krstenje; особе и шифарници се праве овим редом."""
        dete_ime, otac_prezime = _obavezna_imena(r)
        hram = self._hram.get(r.hram_naziv) or self._hram.get("Непознат храм")
        svestenik = self._svestenik(r)
        otac_vera, otac_narod, majka_vera, majka_narod = (
            self._rasclani_vera_narod_parents(r)
        )
        dete = self._dodaj_dete(r, dete_ime, otac_prezime)
        otac = self._dodaj_oca(r, otac_prezime, otac_vera, otac_narod)
        majka = self._dodaj_majku(r, otac_prezime, majka_vera, majka_narod)
        kum = self._rasclani_kuma(r)
        self._dopuni_gradjansko_ime(dete, r)
        self._set_addresses(r, dete, otac, majka, kum)
        return {
            "dete": dete,
            "otac": otac,
            "majka": majka,
            "kum": kum,
            "hram": hram,
            "svestenik": svestenik,
            **_podaci_zapisa(r),
        }

    def _svestenik(self, r: KrstenjeZapis) -> Svestenik | None:
        """Само већ увезен свештеник; непознат остаје None.

        Раније је get_or_create правио празан Svestenik (без имена → „  " у
        select2) кад свештеник није постојао; сада непознат свештеник остаје
        None, као у vencanja.py и у складу са skip-blank политиком увоза (#340).
        """
        return self._svestenici.get(r.svestenik_id) if r.svestenik_id else None

    @staticmethod
    def _dodaj_dete(r: KrstenjeZapis, ime: str, prezime: str) -> Osoba:
        """Дете је увек нова особа, са презименом оца."""
        return dodaj_osobu(
            ime=ime,
            prezime=prezime,
            pol="М" if r.dete_pol.strip() == "1" else "Ж",
            datum_rodjenja=r.rodjenje_datum,
            vreme_rodjenja=rasclani_vreme(r.rodjenje_vreme),
            mesto_rodjenja=r.rodjenje_mesto,
        )

    def _dodaj_oca(self, r: KrstenjeZapis, prezime: str, vera, narod) -> Osoba:
        """Отац: постојећа или нова особа."""
        return nadji_dodaj_osobu(
            ime=r.otac_ime.strip(),
            prezime=prezime,
            pol="М",
            zanimanje=self._zanimanje.get(r.otac_zanimanje),
            veroispovest=vera,
            narodnost=narod,
        )

    def _dodaj_majku(self, r: KrstenjeZapis, otac_prezime: str, vera, narod) -> Osoba:
        """Мајка; без удатог презимена у реду добија презиме оца.

        Девојачко презиме се издваја из поља презимена мајке.
        """
        udato, devojacko = izdvoj_devojacko(r.majka_prezime.strip())
        return nadji_dodaj_osobu(
            ime=r.majka_ime.strip(),
            prezime=udato or otac_prezime,
            pol="Ж",
            zanimanje=self._zanimanje.get(r.majka_zanimanje),
            veroispovest=vera,
            narodnost=narod,
            devojacko=devojacko or None,
        )

    @staticmethod
    def _dopuni_gradjansko_ime(dete: Osoba, r: KrstenjeZapis) -> None:
        """Грађанско име детета, ако га ред има а особа још нема."""
        if dete and r.dete_gradjansko_ime.strip() and not dete.gradjansko_ime:
            Osoba.objects.filter(pk=dete.pk).update(
                gradjansko_ime=r.dete_gradjansko_ime.strip()
            )

    def _rasclani_vera_narod_parents(self, r: KrstenjeZapis):
        """Вероисповест и народност оба родитеља.

        Посебна колона народности оца има предност над народношћу из колоне
        вере.
        """
        otac_data, majka_from_otac = rasclani_vera_narodnost(r.otac_veroispovest)
        otac_vera = self._vera.get(otac_data["veroispovest"])
        otac_narod = self._narod.get(otac_data["narodnost"])

        if r.otac_narodnost and r.otac_narodnost.strip():
            narod_parsed, _ = rasclani_vera_narodnost(r.otac_narodnost)
            if narod_parsed["narodnost"]:
                otac_narod = self._narod.get(narod_parsed["narodnost"])

        majka_vera, majka_narod = self._vera_narod_majke(
            r, majka_from_otac, otac_vera, otac_narod
        )
        return otac_vera, otac_narod, majka_vera, majka_narod

    def _vera_narod_majke(
        self, r: KrstenjeZapis, majka_from_otac, otac_vera, otac_narod
    ):
        """Вера и народност мајке: њена колона, па део из колоне оца, па очеве."""
        if r.majka_veroispovest and r.majka_veroispovest.strip():
            majka_data, _ = rasclani_vera_narodnost(r.majka_veroispovest)
            return (
                self._vera.get(majka_data["veroispovest"]),
                self._narod.get(majka_data["narodnost"]),
            )
        if majka_from_otac:
            return (
                self._vera.get(majka_from_otac["veroispovest"]),
                self._narod.get(majka_from_otac["narodnost"]),
            )
        return otac_vera, otac_narod

    def _rasclani_kuma(self, zapis: KrstenjeZapis) -> Osoba | None:
        """Кум: из имена и презимена, или цепањем пуног имена на последњој речи."""
        puno_ime = zapis.kum_ime.strip()
        if not puno_ime:
            return None

        prezime = zapis.kum_prezime.strip()
        ime, prezime = (puno_ime, prezime) if prezime else podeli_zadnju_rec(puno_ime)

        if not (ime and prezime):
            if self._verbose:
                self.log_warning(f"Неуспело цепање имена кума: '{puno_ime}'")
            return None

        kumu_vencano, kumu_devojacko = izdvoj_devojacko(prezime)
        return nadji_dodaj_osobu(
            ime=ime,
            prezime=kumu_vencano or kumu_devojacko,
            pol=pol_prema_imenu(ime),
            zanimanje=self._zanimanje.get(zapis.kum_zanimanje),
            devojacko=kumu_devojacko or None,
        )

    @staticmethod
    def _set_addresses(
        r: KrstenjeZapis, dete: Osoba, *odrasli_redom: Osoba | None
    ) -> None:
        """Адресе детета, оца, мајке и кума, овим редом.

        Одрасли (отац, мајка, кум) имају у реду само место.
        """
        _dodaj_adresu_deteta(dete, r)
        mesta = (r.otac_adresa, r.majka_adresa, r.kum_mesto)
        for osoba, mesto in zip(odrasli_redom, mesta):
            if osoba and mesto:
                dodaj_adresu(osoba, nadji_dodaj_adresu(mesto=mesto))
