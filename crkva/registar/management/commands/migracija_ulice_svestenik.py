"""Додели свештеника улицама/адресама из старе DBF базе (#26).

Стара база (`crkva.zip` → `HSPULICE.DBF`) чува за сваку улицу шифру свештеника
(`UL_RBRSV`), а свештеничке шифре (`HSPSVEST.SV_RBR`) су при увозу сачуване као
`Svestenik.uid`. Ова команда декодира називе улица (`Konvertor`), мапира
`UL_RBRSV → Svestenik` и поставља `Adresa.svestenik` за све адресе чија се улица
поклапа — основа за извештај васкршње водице по улицама.

    python manage.py migracija_ulice_svestenik --schema crkva_sv_petke_cukarica
    python manage.py migracija_ulice_svestenik --dry-run
"""

from __future__ import annotations

import struct
import zipfile

from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from registar.models import Adresa, Svestenik
from registar.utils.migration_converters import Konvertor


def _read_dbf(raw: bytes):
    """Минимални DBF читач: враћа листу dict-ова по запису.

    Подржава типове C (стринг) и I (little-endian int4); остале враћа као сиров
    стрипован стринг. Брисани записи (флаг 0x2A) се прескачу.
    """
    nrec = struct.unpack("<I", raw[4:8])[0]
    hlen = struct.unpack("<H", raw[8:10])[0]
    rlen = struct.unpack("<H", raw[10:12])[0]
    fields = []
    pos = 32
    while raw[pos] != 0x0D:
        name = raw[pos : pos + 11].split(b"\x00")[0].decode("latin1")
        ftype = chr(raw[pos + 11])
        flen = raw[pos + 16]
        fields.append((name, ftype, flen))
        pos += 32
    rows = []
    for i in range(nrec):
        rec = raw[hlen + i * rlen : hlen + (i + 1) * rlen]
        if not rec or rec[0:1] == b"\x2a":  # deleted
            continue
        off = 1
        row = {}
        for name, ftype, flen in fields:
            chunk = rec[off : off + flen]
            off += flen
            if ftype == "I" and flen == 4:
                row[name] = struct.unpack("<i", chunk)[0]
            elif ftype == "C":
                row[name] = chunk.decode("latin1").rstrip("\x00").strip()
            else:
                row[name] = chunk.decode("latin1").strip()
        rows.append(row)
    return rows


def _norm(ulica: str) -> str:
    """Кључ за поклапање улица: без вишка размака, без водеће/пратеће интерпункције, lower."""
    return " ".join((ulica or "").split()).strip().lower()


class Command(BaseCommand):
    help = "Додели свештеника улицама/адресама из старе DBF базе (UL_RBRSV)."

    def add_arguments(self, parser):
        parser.add_argument("--zip", default="crkva.zip", help="Путања до crkva.zip")
        parser.add_argument(
            "--schema",
            default="crkva_sv_petke_cukarica",
            help="Парохијска шема (tenant) у којој се додела врши.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Само прикажи план доделе, без уписа.",
        )

    def handle(self, *args, **opts):
        zip_path = opts["zip"]
        schema = opts["schema"]
        dry = opts["dry_run"]

        with zipfile.ZipFile(zip_path) as z:
            names = {n.split("/")[-1].upper(): n for n in z.namelist()}
            ulice = _read_dbf(z.read(names["HSPULICE.DBF"]))

        # Декодуј називе улица и задржи оне са додељеним свештеником.
        # Иста улица може имати више редова (стара база је неке улице делила
        # међу свештеницима по бројевима); такве сматрамо конфликтним и
        # прескачемо (додела по самом називу не може да их раздвоји).
        by_street = {}  # norm -> {"naziv": str, "priests": set(rbrsv)}
        for u in ulice:
            rbrsv = u.get("UL_RBRSV") or 0
            naziv = Konvertor.string(u.get("UL_NAZIV") or "")
            if not (rbrsv and naziv):
                continue
            entry = by_street.setdefault(
                _norm(naziv), {"naziv": naziv, "priests": set()}
            )
            entry["priests"].add(rbrsv)

        self.stdout.write(
            f"Улица са додељеним свештеником у старој бази: {len(by_street)}"
        )

        with schema_context(schema):
            # Мапа: норм. назив улице (тренутна база) → списак Adresa
            adrese_by_ulica = {}
            for a in Adresa.objects.all():
                adrese_by_ulica.setdefault(_norm(a.ulica), []).append(a)

            svestenici = {s.uid: s for s in Svestenik.objects.all()}

            assigned_addr = 0
            matched_streets = 0
            unmatched_streets = []
            missing_priest = []
            conflict_streets = []

            for norm_key, entry in by_street.items():
                naziv = entry["naziv"]
                priest_ids = entry["priests"]
                if len(priest_ids) > 1:
                    # Улица подељена међу више свештеника — не можемо по називу.
                    conflict_streets.append(naziv)
                    continue
                rbrsv = next(iter(priest_ids))
                svestenik = svestenici.get(rbrsv)
                if svestenik is None:
                    missing_priest.append((naziv, rbrsv))
                    continue
                adrese = adrese_by_ulica.get(norm_key, [])
                if not adrese:
                    unmatched_streets.append(naziv)
                    continue
                matched_streets += 1
                for a in adrese:
                    if a.svestenik_id != svestenik.uid:
                        a.svestenik = svestenik
                        if not dry:
                            a.save(update_fields=["svestenik"])
                        assigned_addr += 1
                self.stdout.write(
                    f"  {naziv} → {svestenik.ime} {svestenik.prezime} "
                    f"({len(adrese)} адр.)"
                )

            self.stdout.write("")
            self.stdout.write(
                f"{'[DRY-RUN] ' if dry else ''}Поклопљено улица: {matched_streets}; "
                f"ажурирано адреса: {assigned_addr}"
            )
            if conflict_streets:
                self.stdout.write(
                    self.style.WARNING(
                        f"Подељене улице — прескочене, додела ручно ({len(conflict_streets)}): "
                        + ", ".join(conflict_streets)
                    )
                )
            if unmatched_streets:
                self.stdout.write(
                    self.style.WARNING(
                        f"Неупарене улице ({len(unmatched_streets)}): "
                        + ", ".join(unmatched_streets)
                    )
                )
            if missing_priest:
                self.stdout.write(
                    self.style.WARNING(
                        f"Без свештеника у новој бази ({len(missing_priest)}): "
                        + ", ".join(f"{n}#{r}" for n, r in missing_priest)
                    )
                )
