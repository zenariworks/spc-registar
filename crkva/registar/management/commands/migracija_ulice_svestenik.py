"""Додели свештеника улицама/адресама из старе DBF базе (#26).

Стара база (`crkva.zip` → `HSPULICE.DBF`) чува за сваку улицу шифру свештеника
(`UL_RBRSV`), а свештеничке шифре (`HSPSVEST.SV_RBR`) су при увозу сачуване као
`Svestenik.uid`. Ова команда декодира називе улица, мапира
`UL_RBRSV → Svestenik` и поставља `Adresa.svestenik` за све адресе чија се улица
поклапа — основа за извештај васкршње водице по улицама.

    python manage.py migracija_ulice_svestenik --schema crkva_sv_petke_cukarica
    python manage.py migracija_ulice_svestenik --schema crkva_sv_petke_cukarica --dry-run
"""

from __future__ import annotations

import struct
import zipfile
from dataclasses import dataclass, field

from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from registar.models import Adresa, Svestenik
from registar.utils.preslovljavanje import preslovi

DBF_ENCODING = "cp1250"
"""Исто кодирање као `load_dbf` (dbfread encoding="cp1250").

Називи улица овде декодирају идентично онима сачуваним у `Adresa.ulica` (#336).
Стари подаци су 7-битни YUSCII (ASCII опсег), па је за постојећу базу резултат
исти као латиница-1; поравнање уклања латентни расцеп за евентуалне 8-битне
бајтове.
"""

DBF_OBRISAN = b"\x2a"
DBF_KRAJ_ZAGLAVLJA = 0x0D


def _dbf_polja(raw: bytes) -> list[tuple[str, str, int]]:
    """Опис поља из DBF заглавља: (назив, тип, дужина)."""
    fields = []
    pos = 32
    while raw[pos] != DBF_KRAJ_ZAGLAVLJA:
        name = raw[pos : pos + 11].split(b"\x00")[0].decode(DBF_ENCODING)
        fields.append((name, chr(raw[pos + 11]), raw[pos + 16]))
        pos += 32
    return fields


def _dbf_vrednost(ftype: str, flen: int, chunk: bytes):
    """Вредност једног поља: I као little-endian int4, остало као текст."""
    if ftype == "I" and flen == 4:
        return struct.unpack("<i", chunk)[0]
    text = chunk.decode(DBF_ENCODING)
    if ftype == "C":
        return text.rstrip("\x00").strip()
    return text.strip()


def _dbf_zapis(rec: bytes, fields: list[tuple[str, str, int]]) -> dict:
    """Један запис као dict; први бајт је ознака брисања."""
    row = {}
    off = 1
    for name, ftype, flen in fields:
        row[name] = _dbf_vrednost(ftype, flen, rec[off : off + flen])
        off += flen
    return row


def _read_dbf(raw: bytes):
    """Минимални DBF читач: враћа листу dict-ова по запису.

    Подржава типове C (стринг) и I (little-endian int4); остале враћа као сиров
    стрипован стринг. Брисани записи (флаг 0x2A) се прескачу.
    """
    nrec, hlen, rlen = struct.unpack("<IHH", raw[4:12])
    fields = _dbf_polja(raw)
    rows = []
    for i in range(nrec):
        rec = raw[hlen + i * rlen : hlen + (i + 1) * rlen]
        if rec and rec[0:1] != DBF_OBRISAN:
            rows.append(_dbf_zapis(rec, fields))
    return rows


def _norm(ulica: str) -> str:
    """Кључ за поклапање улица: без вишка размака, без водеће/пратеће интерпункције, lower."""
    return " ".join((ulica or "").split()).strip().lower()


def _ulice_sa_svestenikom(ulice: list[dict]) -> dict[str, dict]:
    """Улице са додељеним свештеником, по нормализованом називу.

    Враћа `norm → {"naziv": str, "priests": set(UL_RBRSV)}`. Иста улица може
    имати више редова (стара база је неке улице делила међу свештеницима по
    бројевима); тада `priests` има више шифара и улица је конфликтна.
    """
    po_ulici = {}
    for u in ulice:
        rbrsv = u.get("UL_RBRSV") or 0
        naziv = preslovi(u.get("UL_NAZIV") or "")
        if not (rbrsv and naziv):
            continue
        unos = po_ulici.setdefault(_norm(naziv), {"naziv": naziv, "priests": set()})
        unos["priests"].add(rbrsv)
    return po_ulici


def _postavi_svestenika(adrese: list[Adresa], svestenik: Svestenik, dry: bool) -> int:
    """Поставља свештеника адресама које га немају; враћа број измењених."""
    izmenjeno = 0
    for a in adrese:
        if a.svestenik_id != svestenik.uid:
            a.svestenik = svestenik
            if not dry:
                a.save(update_fields=["svestenik"])
            izmenjeno += 1
    return izmenjeno


@dataclass
class _Ishod:
    """Збир доделе за завршни извештај."""

    pronadjene_ulice: int = 0
    dodeljena_adresa: int = 0
    konfliktne_ulice: list[str] = field(default_factory=list)
    nepronadjene_ulice: list[str] = field(default_factory=list)
    nepronadjeni_svestenici: list[tuple[str, int]] = field(default_factory=list)


class Command(BaseCommand):
    help = "Додели свештеника улицама/адресама из старе DBF базе (UL_RBRSV)."

    def add_arguments(self, parser):
        parser.add_argument("--zip", default="crkva.zip", help="Путања до crkva.zip")
        parser.add_argument(
            "--schema",
            required=True,
            help="Парохијска шема (tenant) у којој се додела врши "
            "(обавезно — нема подразумеване продукцијске шеме, #336).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Само прикажи план доделе, без уписа.",
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        with zipfile.ZipFile(opts["zip"]) as z:
            names = {n.split("/")[-1].upper(): n for n in z.namelist()}
            ulice = _read_dbf(z.read(names["HSPULICE.DBF"]))

        po_ulici = _ulice_sa_svestenikom(ulice)
        self.stdout.write(
            f"Улица са додељеним свештеником у старој бази: {len(po_ulici)}"
        )

        with schema_context(opts["schema"]):
            ishod = self._dodeli(po_ulici, dry)
        self._izvestaj(ishod, dry)

    def _dodeli(self, po_ulici: dict[str, dict], dry: bool) -> _Ishod:
        """Додељује свештеника адресама сваке улице која има тачно једног.

        Улица подељена међу више свештеника не може да се раздвоји по самом
        називу, па се прескаче и пријављује за ручну доделу.
        """
        adrese_po_ulici = {}
        for a in Adresa.objects.all():
            adrese_po_ulici.setdefault(_norm(a.ulica), []).append(a)
        svestenici = {s.uid: s for s in Svestenik.objects.all()}

        ishod = _Ishod()
        for norm_key, unos in po_ulici.items():
            naziv = unos["naziv"]
            if len(unos["priests"]) > 1:
                ishod.konfliktne_ulice.append(naziv)
                continue
            rbrsv = next(iter(unos["priests"]))
            svestenik = svestenici.get(rbrsv)
            if svestenik is None:
                ishod.nepronadjeni_svestenici.append((naziv, rbrsv))
                continue
            adrese = adrese_po_ulici.get(norm_key, [])
            if not adrese:
                ishod.nepronadjene_ulice.append(naziv)
                continue
            ishod.pronadjene_ulice += 1
            ishod.dodeljena_adresa += _postavi_svestenika(adrese, svestenik, dry)
            self.stdout.write(
                f"  {naziv} → {svestenik.ime} {svestenik.prezime} "
                f"({len(adrese)} адр.)"
            )
        return ishod

    def _izvestaj(self, ishod: _Ishod, dry: bool) -> None:
        """Завршни збир и упозорења за улице које нису додељене."""
        self.stdout.write("")
        self.stdout.write(
            f"{'[DRY-RUN] ' if dry else ''}Поклопљено улица: {ishod.pronadjene_ulice}; "
            f"ажурирано адреса: {ishod.dodeljena_adresa}"
        )
        upozorenja = (
            ("Подељене улице — прескочене, додела ручно", ishod.konfliktne_ulice),
            ("Неупарене улице", ishod.nepronadjene_ulice),
            (
                "Без свештеника у новој бази",
                [f"{n}#{r}" for n, r in ishod.nepronadjeni_svestenici],
            ),
        )
        for naslov, stavke in upozorenja:
            if stavke:
                self.stdout.write(
                    self.style.WARNING(
                        f"{naslov} ({len(stavke)}): " + ", ".join(stavke)
                    )
                )
