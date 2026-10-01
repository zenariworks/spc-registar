"""One-shot cleanup of duplicate Osoba rows.

Спаја дупле особе истог имена/презимена уз сигурне сигнале:
  - исти tel_fiksni или tel_mobilni, ИЛИ
  - иста канонска Adresa, ИЛИ
  - иста Adresa домаћинства
Несигурне групе се пријављују за људски преглед, не дирају се.

Раније је команда имала и Фазу 1 (Adresa) и Фазу 2 (Domacinstvo), али су обе
биле мртве на исправном увозу (#354): `Adresa` има unique индекс на
(ulica, broj, broj_stana, mesto) па дупле адресе не могу да постоје, а дупла
домаћинства по домаћину настају тек кад Osoba merge направи истог домаћина —
што сама фаза особа решава преко `_merge_dom_into`.

Usage:
  manage.py popravi_duplikate --dry-run
  manage.py popravi_duplikate --schema crkva_sv_petke_cukarica
"""
# pylint: disable=missing-function-docstring,too-many-locals,broad-exception-caught

from __future__ import annotations

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from registar.management.commands._schema_target import razresi_ciljne_sheme
from registar.models import Domacinstvo, Osoba, Ukucanin
from registar.models.krstenje import Krstenje
from registar.models.vencanje import Vencanje

POLJA_POPUNJENOSTI = (
    "pol",
    "datum_rodjenja",
    "mesto_rodjenja",
    "adresa_id",
    "tel_fiksni",
    "tel_mobilni",
    "zanimanje_id",
    "veroispovest_id",
    "narodnost_id",
    "devojacko",
    "gradjansko_ime",
)

POLJA_DOPUNE_OSOBE = (
    "pol",
    "datum_rodjenja",
    "mesto_rodjenja",
    "vreme_rodjenja",
    "devojacko",
    "gradjansko_ime",
    "adresa_id",
    "tel_fiksni",
    "tel_mobilni",
    "zanimanje_id",
    "veroispovest_id",
    "narodnost_id",
    "parohijan",
)

POLJA_DOPUNE_DOMACINSTVA = (
    "adresa_id",
    "slava_id",
    "tel_fiksni",
    "tel_mobilni",
    "napomena",
    "slavska_vodica",
    "vaskrsnja_vodica",
)

OSOBA_FKS = [
    (Krstenje, ["dete", "otac", "majka", "kum"]),
    (
        Vencanje,
        [
            "zenik",
            "nevesta",
            "kum",
            "svekar",
            "svekrva",
            "tast",
            "tasta",
            "stari_svat",
        ],
    ),
]


def _norm(s):
    return (s or "").strip().lower()


def _osoba_key(p: Osoba) -> tuple:
    return (_norm(p.ime), _norm(p.prezime))


def _popunjenost(p: Osoba) -> int:
    """Колико је запис особе потпун: број попуњених POLJA_POPUNJENOSTI.

    Парохијан вреди 2. Од дупликата канонска остаје особа са највећом
    попуњеношћу.
    """
    score = sum(1 for fld in POLJA_POPUNJENOSTI if getattr(p, fld, None))
    if p.parohijan:
        score += 2
    return score


def _dopuni_prazna_polja(cilj, izvor, polja) -> None:
    """Препиши у `cilj` вредности из `izvor` за поља која су у `cilj` празна."""
    for f in polja:
        if not getattr(cilj, f) and getattr(izvor, f):
            setattr(cilj, f, getattr(izvor, f))


def _signal(p: Osoba, adrese_domacinstava: dict) -> tuple | None:
    """Најјачи сигнал идентитета особе, по приоритету.

    Фиксни телефон, па мобилни, па канонска адреса, па адреса домаћинства
    чији је особа домаћин. `None` ако особа нема ниједан.
    """
    if p.tel_fiksni:
        return ("tel_fiksni", str(p.tel_fiksni))
    if p.tel_mobilni:
        return ("tel_mobilni", str(p.tel_mobilni))
    if p.adresa_id:
        return ("adresa", p.adresa_id)
    if adrese_domacinstava.get(p.pk):
        return ("dom_adresa", adrese_domacinstava[p.pk])
    return None


def _adrese_domacinstava(osobe: list[Osoba]) -> dict:
    """uid домаћина → adresa_id његовог домаћинства (само где адреса постоји)."""
    return {
        d.domacin_id: d.adresa_id
        for d in Domacinstvo.objects.filter(domacin__in=osobe).only(
            "domacin_id", "adresa_id"
        )
        if d.adresa_id
    }


def _podeli_po_signalu(osobe: list[Osoba]) -> tuple[dict, list[Osoba]]:
    """Подели особе истог имена у подгрупе по сигналу; врати и оне без сигнала."""
    adrese = _adrese_domacinstava(osobe)
    podgrupe: dict = defaultdict(list)
    bez_signala = []
    for p in osobe:
        sig = _signal(p, adrese)
        if sig is None:
            bez_signala.append(p)
        else:
            podgrupe[sig].append(p)
    return podgrupe, bez_signala


class Command(BaseCommand):
    help = "Спајање дупликата особа"

    OSOBA_FKS = OSOBA_FKS

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Само пријави, не мењај базу"
        )
        parser.add_argument("--schema", help="Само за дати tenant schema")
        parser.add_argument(
            "--all-tenants",
            action="store_true",
            help=(
                "Покрени над СВИМ закупцима (осим public). Опасно — "
                "подразумевано се ради само над активном шемом (#330)."
            ),
        )

    def handle(self, *args, **opts):
        from django_tenants.utils import get_tenant_model, tenant_context

        tenant_model = get_tenant_model()
        dry = opts["dry_run"]

        for ime_sheme in razresi_ciljne_sheme(opts):
            zakupac = tenant_model.objects.get(schema_name=ime_sheme)
            self.stdout.write(
                self.style.MIGRATE_HEADING(f"\n=== {ime_sheme} (dry-run={dry}) ===")
            )
            with tenant_context(zakupac):
                self._phase_osoba(dry_run=dry)

    def _merge_dom_into(self, canonical: Domacinstvo, dupe: Domacinstvo):
        _dopuni_prazna_polja(canonical, dupe, POLJA_DOPUNE_DOMACINSTVA)
        canonical.save()
        self._move_ukucani(canonical, dupe)
        dupe.delete()

    def _move_ukucani(self, canonical: Domacinstvo, dupe: Domacinstvo):
        """Пребаци укућане из `dupe` у `canonical`.

        Ред чија је особа већ укућанин у `canonical` се брише уместо да
        прекрши `unique_osoba_per_domacinstvo`.
        """
        canon_osobe = set(
            Ukucanin.objects.filter(domacinstvo=canonical).values_list(
                "osoba_id", flat=True
            )
        )
        for u in Ukucanin.objects.filter(domacinstvo=dupe):
            if u.osoba_id in canon_osobe:
                u.delete()
            else:
                u.domacinstvo = canonical
                u.save(update_fields=["domacinstvo"])

    def _phase_osoba(self, dry_run: bool):
        """Спаја особе истог имена по подгрупама истог сигнала.

        Свака подгрупа са бар две особе се спаја у најбогатију од њих;
        особе без пара (без сигнала или са јединственим сигналом) иду на
        људски преглед. Група не мора цела да дели један сигнал — ред 1 може
        да дели сигнал А, а редови 2 и 3 сигнал Б.
        """
        self.stdout.write(self.style.MIGRATE_LABEL("\n— Спајање дупликата особа —"))
        merged = 0
        reported = []
        for k, osobe in self._grupe_istog_imena().items():
            spojeno, za_pregled = self._obradi_grupu(osobe, dry_run)
            merged += spojeno
            if za_pregled:
                reported.append((k, za_pregled))
        self._izvestaj(merged, reported, dry_run)

    def _grupe_istog_imena(self) -> dict:
        """Групе од бар две особе истог (нормализованог) имена и презимена."""
        groups = defaultdict(list)
        for p in Osoba.objects.all():
            k = _osoba_key(p)
            if k != ("", ""):
                groups[k].append(p)
        return {k: lst for k, lst in groups.items() if len(lst) >= 2}

    def _obradi_grupu(self, osobe: list[Osoba], dry_run: bool) -> tuple[int, list]:
        """Спој подгрупе једне групе; врати број спојених и особе за преглед."""
        podgrupe, za_pregled = _podeli_po_signalu(osobe)
        merged = 0
        delimicno = False
        for clanovi in podgrupe.values():
            if len(clanovi) < 2:
                za_pregled.extend(clanovi)
                delimicno = True
                continue
            merged += self._spoji_podgrupu(clanovi, dry_run)

        if za_pregled and (len(za_pregled) + len(podgrupe) > 1 or delimicno):
            return merged, za_pregled
        return merged, []

    def _spoji_podgrupu(self, clanovi: list[Osoba], dry_run: bool) -> int:
        """Спој све чланове у најбогатијег; врати број спојених (и у dry-run)."""
        canonical = max(clanovi, key=_popunjenost)
        duple = [p for p in clanovi if p.pk != canonical.pk]
        if not dry_run:
            for dupe in duple:
                with transaction.atomic():
                    self._merge_osoba_into(canonical, dupe)
        return len(duple)

    def _izvestaj(self, merged: int, reported: list, dry_run: bool) -> None:
        prefix = "би се" if dry_run else ""
        self.stdout.write(f"  {prefix} спојено {merged} дупл. особа")
        self.stdout.write(
            self.style.WARNING(f"  пријављено за људски преглед: {len(reported)} група")
        )
        for k, lst in reported[:10]:
            detalji = ", ".join(
                f"uid={p.uid}/pol={p.pol or '—'}/tel={p.tel_fiksni or p.tel_mobilni or '—'}"
                for p in lst
            )
            self.stdout.write(f"    '{k[0]} {k[1]}': " + detalji)

    def _merge_osoba_into(self, canonical: Osoba, dupe: Osoba):
        """Спој `dupe` у `canonical` и обриши `dupe`.

        Редом: допуни празна поља, реши судар домаћинстава (OneToOne
        домаћин), пребаци укућане и FK из крштења/венчања, па обриши дупликат
        (каскаде не окидају јер су све везе већ пребачене).
        """
        _dopuni_prazna_polja(canonical, dupe, POLJA_DOPUNE_OSOBE)
        canonical.save()
        self._prebaci_domacinstvo(canonical, dupe)
        self._prebaci_ukucanstva(canonical, dupe)
        for model, fields in self.OSOBA_FKS:
            for fname in fields:
                model.objects.filter(**{fname: dupe}).update(**{fname: canonical})
        dupe.delete()

    def _prebaci_domacinstvo(self, canonical: Osoba, dupe: Osoba) -> None:
        """Домаћинство дупликата постаје канонског, или се спаја са његовим."""
        dupe_dom = Domacinstvo.objects.filter(domacin=dupe).first()
        if not dupe_dom:
            return
        canon_dom = Domacinstvo.objects.filter(domacin=canonical).first()
        if canon_dom and canon_dom.pk != dupe_dom.pk:
            self._merge_dom_into(canon_dom, dupe_dom)
        else:
            dupe_dom.domacin = canonical
            dupe_dom.save()

    def _prebaci_ukucanstva(self, canonical: Osoba, dupe: Osoba) -> None:
        """Укућанства дупликата прелазе на канонску; дупла чланства се бришу."""
        canon_doms = set(
            Ukucanin.objects.filter(osoba=canonical).values_list(
                "domacinstvo_id", flat=True
            )
        )
        for u in Ukucanin.objects.filter(osoba=dupe):
            if u.domacinstvo_id in canon_doms:
                u.delete()
            else:
                u.osoba = canonical
                u.save(update_fields=["osoba"])
