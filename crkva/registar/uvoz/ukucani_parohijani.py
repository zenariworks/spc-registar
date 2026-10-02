"""Миграција домаћинстава и укућана из hsp_domacini + hsp_ukucani.

Креира Osoba (домаћин), Adresa, Domacinstvo, и Ukucanin записе. За разлику
од миграције венчања/крштења, овде имамо две изворне табеле; код је
донекле линеаран, али дели исте помоћнике из `registar.utils.migracija`.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init,too-many-locals,broad-exception-caught,not-callable

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from registar.models import Adresa, Domacinstvo, Osoba, Slava, Ukucanin
from registar.utils.migracija.address import nadji_dodaj_adresu, warm_adresa_cache
from registar.utils.migracija.helpers import cirilica, izdvoj_devojacko
from registar.utils.migracija.osoba_repo import (
    cache_osoba,
    nadji_dodaj_osobu,
    nadji_osobu,
    warm_osoba_cache,
)
from registar.utils.migracija.pol import pol_prema_imenu
from registar.utils.migracija.slava_map import resolve_slava
from registar.uvoz.osnovno import MigrationCommand

DOMACINI_SQL = """
    SELECT "DOM_RBR", "DOM_IME", "DOM_RBRUL", "DOM_BROJ", "DOM_OZNAKA",
           "DOM_STAN", "DOM_TELDIR", "DOM_TELMOB", "DOM_RBRSL",
           "DOM_SLAVOD", "DOM_USKVOD", "DOM_NAPOM"
    FROM hsp_domacini
    WHERE "DOM_RBR" IS NOT NULL AND "DOM_IME" IS NOT NULL
    ORDER BY "DOM_RBR"
"""


@dataclass
class _Domacin:
    """Домаћин из једног реда hsp_domacini, спреман за упис."""

    uid: int
    ime: str
    prezime: str
    devojacko: str
    adresa: Adresa
    tel_f: str | None
    tel_m: str | None


def _ime_domacina(puno_ime: str) -> tuple[str, str, str]:
    """(име, презиме, девојачко) из пуног имена домаћина.

    Домаћин са презименом само у облику „р.<девојачко>“ не може да се направи
    без удатог презимена, па девојачко постаје и презиме — ред се не губи, а
    команда за чишћење (popravi_devojacka) може касније да га поново раздвоји.
    """
    ime, puno_prezime = (puno_ime.split(" ", 1) + [""])[:2]
    vencano, devojacko = izdvoj_devojacko(puno_prezime)
    return ime, vencano or devojacko, devojacko


def _vodica(vrednost: str | None) -> bool:
    """„D“ у колони водице; NULL је False (колоне су NOT NULL, #340)."""
    return bool(vrednost and vrednost.strip() == "D")


def _dopune(osoba: Osoba, d: _Domacin) -> dict:
    """Поља постојеће особе која су празна, а домаћин их има."""
    updates = {} if osoba.parohijan else {"parohijan": True}
    for polje, postojece, novo in (
        ("adresa", osoba.adresa_id, d.adresa),
        ("tel_fiksni", osoba.tel_fiksni, d.tel_f),
        ("tel_mobilni", osoba.tel_mobilni, d.tel_m),
        ("devojacko", osoba.devojacko, d.devojacko),
    ):
        if not postojece and novo:
            updates[polje] = novo
    if not osoba.pol:
        pol = pol_prema_imenu(d.ime)
        if pol:
            updates["pol"] = pol
    return updates


def _osoba_domacina(d: _Domacin) -> tuple[Osoba, bool]:
    """Постојећа особа истог имена са заједничким сигналом, или нова.

    Пореди се са СВИМ особама истог имена у кешу и спаја у прву која дели
    сигнал (адреса, фиксни или мобилни). Тако ред #3 који дели сигнал са
    редом #2 (а не са #1) и даље бива спојен уместо да се направи нова особа.
    Постојећој особи се допуњују само празна поља.
    """
    osoba = nadji_osobu(d.ime, d.prezime, adresa=d.adresa, tel_f=d.tel_f, tel_m=d.tel_m)
    if osoba is None:
        return Osoba.objects.get_or_create(
            uid=d.uid,
            defaults={
                "ime": d.ime,
                "prezime": d.prezime,
                "devojacko": d.devojacko or None,
                "parohijan": True,
                "adresa": d.adresa,
                "tel_fiksni": d.tel_f,
                "tel_mobilni": d.tel_m,
                "pol": pol_prema_imenu(d.ime),
            },
        )
    updates = _dopune(osoba, d)
    if updates:
        Osoba.objects.filter(pk=osoba.pk).update(**updates)
        osoba.refresh_from_db()
    return osoba, False


class Command(MigrationCommand):
    help = "Миграција домаћинстава и укућана из hsp_domacini и hsp_ukucani"

    staging_tables = ["hsp_domacini", "hsp_ukucani"]
    target_model = Ukucanin

    def handle(self, *args, **opts) -> None:
        self.zabrani_nad_public()
        self._dry_run = opts.get("dry_run", False)
        limit: int = opts.get("limit", 0) or 0

        if not self._dry_run:
            self.stdout.write("Чишћење постојећих података...")
            Ukucanin.objects.all().delete()
            Domacinstvo.objects.all().delete()

        n_adr = warm_adresa_cache()
        n_os = warm_osoba_cache()
        self.stdout.write(f"Загрејано: {n_adr} адреса, {n_os} особа у кешу.")

        self.stdout.write("Учитавам називе улица из hsp_ulice...")
        self.ulice_cache = self._build_ulice_cache()
        self.stdout.write(f"Учитано {len(self.ulice_cache)} улица.")

        self.stdout.write("Креирам парохијане и домаћинства...")
        self._create_parohijani_and_domacinstva(limit=limit)

        if not self._dry_run:
            self._resetuj_sekvencu_osoba()

        self.stdout.write("Креирам укућане...")
        records = self.take(self._prepare_ukucanin_records(), limit)
        created = self.migrate_in_batches(
            records, batch_size=1000, dry_run=self._dry_run
        )
        self.log_success(created, table_name="укућана")
        if self._dry_run:
            self.log_warning("DRY RUN — ништа није уписано у базу.")
        else:
            self._drop_staging_tables()

    def _resetuj_sekvencu_osoba(self) -> None:
        """Аутоинкремент особа после уписа домаћина са задатим uid-овима."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence('osobe', 'uid'), "
                "(SELECT COALESCE(MAX(uid), 1) FROM osobe))"
            )
        self.stdout.write("Ресетован аутоинкремент за осoбе.")

    def _build_ulice_cache(self) -> Dict[int, str]:
        cache: Dict[int, str] = {}
        with connection.cursor() as cursor:
            cursor.execute('SELECT "UL_SIFRA", "UL_NAZIV" FROM hsp_ulice')
            for sifra_raw, naziv_raw in cursor.fetchall():
                sifra = int(sifra_raw) if sifra_raw else 0
                naziv = cirilica(naziv_raw or "")
                if sifra and naziv:
                    cache[sifra] = naziv
        return cache

    def _create_parohijani_and_domacinstva(self, limit: int = 0) -> None:
        """Пролаз кроз домаћине: особа, адреса и домаћинство по реду.

        Попуњава и `_dbf_uid_to_osoba_uid` (DBF шифра домаћина → uid особе),
        преко које пролаз укућана налази домаћинство и за спојене домаћине.
        Хватају се само грешке података; OperationalError, ProgrammingError
        и KeyboardInterrupt прекидају увоз уместо да се тихо забележе.
        """
        dodato_parohijana = 0
        dodato_domacinstava = 0
        self._dbf_uid_to_osoba_uid: Dict[int, int] = {}

        for row in self._domacini(limit):
            try:
                ishod = self._obradi_domacina(row)
            except (ValueError, IntegrityError, ValidationError) as e:
                self.log_error(f"Грешка за домаћина UID {row[0]}: {e}")
                continue
            if ishod is not None:
                dodato_parohijana += ishod[0]
                dodato_domacinstava += ishod[1]

        self.stdout.write(
            f"Креирано {dodato_parohijana} парохијана и {dodato_domacinstava} домаћинстава."
        )

    @staticmethod
    def _domacini(limit: int) -> list[tuple]:
        """Редови hsp_domacini по шифри, највише `limit` (0 = сви)."""
        with connection.cursor() as cursor:
            cursor.execute(DOMACINI_SQL)
            rows = cursor.fetchall()
        return rows[:limit] if limit else rows

    def _obradi_domacina(self, row: tuple) -> tuple[bool, bool] | None:
        """Упис једног домаћина; враћа (нова особа, ново домаћинство) или None.

        Особа и домаћинство иду у исту трансакцију: ако упис домаћинства падне,
        поништава се и особа, да ред не остане напола направљен. Кеш, мапа
        DBF шифри и бројачи се ажурирају тек после успешног commit-а, да не
        показују на поништену особу (#340).
        """
        (
            uid_raw,
            puno_ime,
            ulica_uid_raw,
            broj_ulice,
            _oznaka_ulice,
            broj_stana,
            telefon_fiksni,
            telefon_mobilni,
            slava_uid_raw,
            slavska_vodica,
            uskrsnja_vodica,
            napomena,
        ) = row
        parohijan_uid = int(uid_raw)
        ulica_uid = int(ulica_uid_raw) if ulica_uid_raw else None
        slava_uid = int(slava_uid_raw) if slava_uid_raw else None

        puno_ime = cirilica(puno_ime)
        if not puno_ime:
            return None
        ime, prezime, devojacko = _ime_domacina(puno_ime)
        if not ime or not prezime:
            self.log_skip(f"Парохијан UID {parohijan_uid}: непотпуно име '{puno_ime}'")
            return None
        if self._dry_run:
            return True, True

        d = _Domacin(
            uid=parohijan_uid,
            ime=ime,
            prezime=prezime,
            devojacko=devojacko,
            adresa=self._adresa(ulica_uid, broj_ulice, broj_stana, napomena),
            tel_f=(telefon_fiksni or "").strip() or None,
            tel_m=(telefon_mobilni or "").strip() or None,
        )
        slava = resolve_slava(slava_uid, Slava)

        with transaction.atomic():
            osoba, p_created = _osoba_domacina(d)
            _, d_created = Domacinstvo.objects.get_or_create(
                domacin=osoba,
                defaults={
                    "adresa": d.adresa,
                    "slava": slava,
                    "tel_fiksni": d.tel_f,
                    "tel_mobilni": d.tel_m,
                    "slavska_vodica": _vodica(slavska_vodica),
                    "vaskrsnja_vodica": _vodica(uskrsnja_vodica),
                    "napomena": cirilica(napomena or ""),
                },
            )

        cache_osoba(osoba)
        self._dbf_uid_to_osoba_uid[parohijan_uid] = osoba.uid
        return p_created, d_created

    def _adresa(self, ulica_uid, broj_ulice, broj_stana, napomena) -> Adresa:
        """Адреса домаћина на Чукарици, са називом улице из hsp_ulice."""
        ulica_naziv = self.ulice_cache.get(ulica_uid, "") if ulica_uid else ""
        return nadji_dodaj_adresu(
            ulica=ulica_naziv,
            broj=cirilica(str(broj_ulice or "")),
            broj_stana=cirilica(str(broj_stana or "")),
            mesto="Чукарица",
            sprat="",
            primedba=cirilica(napomena or ""),
        )

    def _prepare_ukucanin_records(self) -> Iterable[dict | None]:
        """Подаци за Ukucanin по реду hsp_ukucani; None за ред који се прескаче."""
        domacinstva = self._domacinstva_po_dbf_uid()
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "UK_RBRDOM", "UK_IME" FROM hsp_ukucani ORDER BY "UK_RBRDOM"'
            )
            for uid_raw, ime_raw in cursor.fetchall():
                yield self._ukucanin(uid_raw, ime_raw, domacinstva)

    def _domacinstva_po_dbf_uid(self) -> Dict[int, Domacinstvo]:
        """DBF шифра домаћина → домаћинство, преко особе.

        Иде преко uid-а особе, па и спојени (дедуплицирани) домаћини налазе
        своје укућане.
        """
        osoba_to_dom: Dict[int, Domacinstvo] = {
            d.domacin.uid: d for d in Domacinstvo.objects.select_related("domacin")
        }
        return {
            dbf_uid: osoba_to_dom[osoba_uid]
            for dbf_uid, osoba_uid in self._dbf_uid_to_osoba_uid.items()
            if osoba_uid in osoba_to_dom
        }

    def _ukucanin(
        self, uid_raw, ime_raw, domacinstva: Dict[int, Domacinstvo]
    ) -> dict | None:
        """Укућанин са презименом домаћина; „+“ испред имена значи преминуо."""
        uid = int(uid_raw) if uid_raw else 0
        raw_ime = cirilica(ime_raw or "")
        domacinstvo = domacinstva.get(uid) if uid else None
        if domacinstvo is None or not raw_ime:
            return None

        prezime = domacinstvo.domacin.prezime
        preminuo = raw_ime.startswith("+")
        ime = raw_ime[1:].strip() if preminuo else raw_ime

        osoba = nadji_dodaj_osobu(
            ime, prezime, parohijan=False, pol=pol_prema_imenu(ime)
        )
        if not osoba:
            self.log_skip(f"Не могу креирати особу: {ime} {prezime}")
            return None
        return {
            "domacinstvo": domacinstvo,
            "osoba": osoba,
            "ime_ukucana": ime,
            "preminuo": preminuo,
        }

    def _drop_staging_tables(self) -> None:
        with connection.cursor() as cursor:
            for table in self.staging_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                self.stdout.write(
                    self.style.SUCCESS(f"Обрисана staging табела '{table}'.")
                )
