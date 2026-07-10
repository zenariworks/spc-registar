"""One-shot cleanup of duplicate Adresa / Domacinstvo / Osoba rows.

Phases:
  1. Adresa: collapse rows with identical (ulica, broj, broj_stana, mesto)
  2. Domacinstvo: merge Domacinstva that share the same domacin Osoba
     (only reachable AFTER Phase 3 merges domacin-Osoba duplicates;
      kept separate so each phase can be inspected/dry-run alone)
  3. Osoba: merge duplicate Osobe with safe signals:
        - identical tel_fiksni or tel_mobilni, OR
        - identical canonical Adresa (after Phase 1), OR
        - identical Domacinstvo Adresa
     Unsafe groups are reported, not touched.

Usage:
  manage.py popravi_duplikate --dry-run
  manage.py popravi_duplikate --phase 1
  manage.py popravi_duplikate --phase all
"""
# pylint: disable=missing-function-docstring,too-many-locals,broad-exception-caught

from __future__ import annotations

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from registar.management.commands._schema_target import razresi_ciljne_sheme
from registar.models import Adresa, Domacinstvo, Osoba, Ukucanin
from registar.models.krstenje import Krstenje
from registar.models.vencanje import Vencanje


def _norm(s):
    return (s or "").strip().lower()


def _adresa_key(a: Adresa) -> tuple:
    return (_norm(a.ulica), _norm(a.broj), _norm(a.broj_stana), _norm(a.mesto))


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
        "devojacko_prezime",
        "gradjansko_ime",
    ):
        if getattr(p, fld, None):
            score += 1
    if p.parohijan:
        score += 2
    # tie-breaker: lower uid = older = more likely the original
    return score


def _domacinstvo_richness(d: Domacinstvo) -> int:
    score = 0
    for fld in ("adresa_id", "slava_id", "tel_fiksni", "tel_mobilni", "napomena"):
        if getattr(d, fld, None):
            score += 1
    if d.slavska_vodica:
        score += 1
    if d.vaskrsnja_vodica:
        score += 1
    return score


class Command(BaseCommand):
    help = "Спајање дупликата за Адресу, Домаћинство и Особу"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Само пријави, не мењај базу"
        )
        parser.add_argument(
            "--phase",
            choices=["1", "2", "3", "all"],
            default="all",
            help="Фаза за извршавање",
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
        phase = opts["phase"]

        for ime_sheme in razresi_ciljne_sheme(opts):
            zakupac = tenant_model.objects.get(schema_name=ime_sheme)
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"\n=== {ime_sheme} (dry-run={dry}, phase={phase}) ==="
                )
            )
            with tenant_context(zakupac):
                if phase in ("1", "all"):
                    self._phase_adresa(dry_run=dry)
                if phase in ("2", "all"):
                    self._phase_domacinstvo(dry_run=dry)
                if phase in ("3", "all"):
                    self._phase_osoba(dry_run=dry)

    # ============================ PHASE 1 ============================ #
    def _phase_adresa(self, dry_run: bool):
        self.stdout.write(self.style.MIGRATE_LABEL("\n— Фаза 1: Адреса —"))
        groups = defaultdict(list)
        for a in Adresa.objects.all().order_by("uid"):
            k = _adresa_key(a)
            if k != ("", "", "", ""):
                groups[k].append(a)

        merged_total = 0
        moved_osoba = 0
        moved_dom = 0
        for k, lst in groups.items():
            if len(lst) < 2:
                continue
            canonical = lst[0]
            dupes = lst[1:]
            dup_ids = [d.uid for d in dupes]
            if dry_run:
                merged_total += len(dupes)
                continue
            with transaction.atomic():
                u = Osoba.objects.filter(adresa_id__in=dup_ids).update(adresa=canonical)
                d = Domacinstvo.objects.filter(adresa_id__in=dup_ids).update(
                    adresa=canonical
                )
                Adresa.objects.filter(uid__in=dup_ids).delete()
                moved_osoba += u
                moved_dom += d
                merged_total += len(dupes)
        if dry_run:
            self.stdout.write(f"  би се обрисало {merged_total} дупликата.")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  обрисано {merged_total} дупликата адресе "
                    f"(пресмерено {moved_osoba} Osoba.adresa, {moved_dom} Domacinstvo.adresa)"
                )
            )

    # ============================ PHASE 2 ============================ #
    def _phase_domacinstvo(self, dry_run: bool):
        """Merge Domacinstva that share the same domacin Osoba (after Phase 3
        merges Osobe, this becomes meaningful; before Phase 3 it's usually a no-op
        because the OneToOne constraint prevents the situation existing already)."""
        self.stdout.write(
            self.style.MIGRATE_LABEL("\n— Фаза 2: Домаћинство (исти домаћин) —")
        )
        groups = defaultdict(list)
        for d in Domacinstvo.objects.select_related("domacin").order_by("created"):
            if d.domacin_id:
                groups[d.domacin_id].append(d)
        n_merged = 0
        for lst in groups.values():
            if len(lst) < 2:
                continue
            canonical = max(lst, key=_domacinstvo_richness)
            for dupe in lst:
                if dupe.pk == canonical.pk:
                    continue
                if dry_run:
                    n_merged += 1
                    continue
                with transaction.atomic():
                    self._merge_dom_into(canonical, dupe)
                    n_merged += 1
        self.stdout.write(
            f"  {'би се' if dry_run else ''} спојено {n_merged} дупл. домаћинстава"
        )

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

        # ============================ PHASE 3 ============================ #

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
        self.stdout.write(self.style.MIGRATE_LABEL("\n— Фаза 3: Особа —"))
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

        self.stdout.write(
            f"  {'би се' if dry_run else ''} спојено {merged} дупл. особа"
        )
        self.stdout.write(
            self.style.WARNING(f"  пријављено за људски преглед: {len(reported)} група")
        )
        for k, lst in reported[:10]:
            print(
                f"    '{k[0]} {k[1]}': "
                + ", ".join(
                    f"uid={p.uid}/pol={p.pol or '—'}/tel={p.tel_fiksni or p.tel_mobilni or '—'}"
                    for p in lst
                )
            )

    def _merge_osoba_into(self, canonical: Osoba, dupe: Osoba):
        # 1. Copy missing fields canonical <- dupe
        for f in (
            "pol",
            "datum_rodjenja",
            "mesto_rodjenja",
            "vreme_rodjenja",
            "devojacko_prezime",
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
