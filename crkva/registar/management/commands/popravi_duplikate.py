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


def _norm(s):
    return (s or "").strip().lower()


def _osoba_key(p: Osoba) -> tuple:
    return (_norm(p.ime), _norm(p.prezime))


def _osoba_richness(p: Osoba) -> int:
    """Higher score = keep this row as canonical."""
    score = 0
    for fld in (
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
    ):
        if getattr(p, fld, None):
            score += 1
    if p.parohijan:
        score += 2
    # tie-breaker: lower uid = older = more likely the original
    return score


class Command(BaseCommand):
    help = "Спајање дупликата особа"

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

    # ------------------------------------------------------------------ #
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

    # ---------------------- спајање домаћинстава ---------------------- #
    def _merge_dom_into(self, canonical: Domacinstvo, dupe: Domacinstvo):
        for f in ("adresa_id", "slava_id", "tel_fiksni", "tel_mobilni", "napomena"):
            if not getattr(canonical, f) and getattr(dupe, f):
                setattr(canonical, f, getattr(dupe, f))
        canonical.slavska_vodica = canonical.slavska_vodica or dupe.slavska_vodica
        canonical.vaskrsnja_vodica = canonical.vaskrsnja_vodica or dupe.vaskrsnja_vodica
        canonical.save()
        self._move_ukucani(canonical, dupe)
        dupe.delete()

    def _move_ukucani(self, canonical: Domacinstvo, dupe: Domacinstvo):
        """Move Ukucanin rows from dupe → canonical, skipping rows that would
        violate the unique_osoba_per_domacinstvo constraint."""
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

    # ---------------------------- особа ------------------------------- #
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

    def _phase_osoba(self, dry_run: bool):
        self.stdout.write(self.style.MIGRATE_LABEL("\n— Спајање дупликата особа —"))
        groups = defaultdict(list)
        for p in Osoba.objects.all():
            k = _osoba_key(p)
            if k != ("", ""):
                groups[k].append(p)

        merged = 0
        reported = []
        for k, lst in groups.items():
            if len(lst) < 2:
                continue
            # Sub-group same-name osobe by safety signal (canonical address,
            # domacinstvo address, fiksni, mobilni). Each sub-group of size >= 2
            # merges into one canonical osoba; remaining singletons are
            # reported for human review. Previous code required the WHOLE
            # group to share one signal, which left partial-match groups
            # (e.g. row1 shares signal A; rows 2+3 share signal B) untouched.
            subgroups: dict = defaultdict(list)
            singletons = []
            dom_by_osoba = {
                d.domacin_id: d.adresa_id
                for d in Domacinstvo.objects.filter(domacin__in=lst).only(
                    "domacin_id", "adresa_id"
                )
                if d.adresa_id
            }
            for p in lst:
                # Pick the strongest signal present, in priority order.
                sig = None
                if p.tel_fiksni:
                    sig = ("tel_fiksni", str(p.tel_fiksni))
                elif p.tel_mobilni:
                    sig = ("tel_mobilni", str(p.tel_mobilni))
                elif p.adresa_id:
                    sig = ("adresa", p.adresa_id)
                elif dom_by_osoba.get(p.pk):
                    sig = ("dom_adresa", dom_by_osoba[p.pk])
                if sig is None:
                    singletons.append(p)
                else:
                    subgroups[sig].append(p)

            partial = False
            for sig, members in subgroups.items():
                if len(members) < 2:
                    singletons.extend(members)
                    partial = True
                    continue
                canonical = max(members, key=_osoba_richness)
                for dupe in members:
                    if dupe.pk == canonical.pk:
                        continue
                    if dry_run:
                        merged += 1
                        continue
                    with transaction.atomic():
                        self._merge_osoba_into(canonical, dupe)
                        merged += 1

            if singletons and (
                len(singletons) + sum(1 for _ in subgroups) > 1 or partial
            ):
                reported.append((k, singletons))

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
            print(f"    '{k[0]} {k[1]}': " + detalji)

    def _merge_osoba_into(self, canonical: Osoba, dupe: Osoba):
        # 1. Copy missing fields canonical <- dupe
        for f in (
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
        ):
            if not getattr(canonical, f) and getattr(dupe, f):
                setattr(canonical, f, getattr(dupe, f))
        if dupe.parohijan and not canonical.parohijan:
            canonical.parohijan = True
        canonical.save()

        # 2. Handle Domacinstvo OneToOne collision
        dupe_dom = Domacinstvo.objects.filter(domacin=dupe).first()
        if dupe_dom:
            canon_dom = Domacinstvo.objects.filter(domacin=canonical).first()
            if canon_dom and canon_dom.pk != dupe_dom.pk:
                self._merge_dom_into(canon_dom, dupe_dom)
            else:
                dupe_dom.domacin = canonical
                dupe_dom.save()

        # 3. Repoint other FKs
        # Move Ukucanin rows, dedupe on collision
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
        for model, fields in self.OSOBA_FKS:
            for fname in fields:
                model.objects.filter(**{fname: dupe}).update(**{fname: canonical})

        # 4. Delete dupe (cascades won't fire because we've moved all refs)
        dupe.delete()
