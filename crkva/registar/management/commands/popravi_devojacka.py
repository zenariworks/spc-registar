"""Накнадно чишћење: раздваја префиксе презимена ``р.<X>`` / ``рођ.<X>`` /
``r.<X>`` у поље ``devojacko``.

DBF увоз је историјски лепио маркер девојачког презимена на поље
``prezime`` — нпр. ``"Татјана р.Бошковић"`` је постало
``ime="Татјана", prezime="р.Бошковић"`` уместо
``prezime="", devojacko="Бошковић"``. ``р.`` је скраћеница за „рођена".

Ова команда налази такве редове и премешта девојачки део у ``devojacko``.
Удато презиме није записано у изворном DBF-у — подразумевано
остављамо ``prezime`` празно да га службеник попуни. Уз
``--keep-married-from-domacinstvo`` покушавамо да закључимо удато
презиме из Домаћинства чији је домаћин друга Osoba са презименом
без префикса.

Употреба:
  manage.py popravi_devojacka --dry-run
  manage.py popravi_devojacka --schema crkva_sv_petke_cukarica
  manage.py popravi_devojacka --keep-married-from-domacinstvo
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,too-many-locals,broad-exception-caught,import-outside-toplevel

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from registar.management.commands._schema_target import razresi_ciljne_sheme
from registar.migracija.helpers import izdvoj_devojacko
from registar.models import Domacinstvo, Osoba, Ukucanin


class Command(BaseCommand):
    help = (
        "Помера маркер 'р.' / 'рођ.' са презимена у девојачко презиме "
        "(чисти лош DBF импорт)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Само пријави, не мењај базу",
        )
        parser.add_argument(
            "--schema",
            help="Само за дати tenant schema (нпр. crkva_sv_petke_cukarica)",
        )
        parser.add_argument(
            "--all-tenants",
            action="store_true",
            help=(
                "Покрени над СВИМ закупцима (осим public). Опасно — "
                "подразумевано се ради само над активном шемом (#330)."
            ),
        )
        parser.add_argument(
            "--keep-married-from-domacinstvo",
            action="store_true",
            help=(
                "Покушај да задржи удато презиме из домаћинства "
                "(од домаћина ако је другачије презиме). "
                "Подразумевано: остави prezime празно."
            ),
        )

    def handle(self, *args, **opts):
        from django_tenants.utils import get_tenant_model, tenant_context

        tenant_model = get_tenant_model()
        dry: bool = opts["dry_run"]
        keep_from_dom: bool = opts["keep_married_from_domacinstvo"]

        for ime_sheme in razresi_ciljne_sheme(opts):
            zakupac = tenant_model.objects.get(schema_name=ime_sheme)
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"\n=== {ime_sheme} (dry-run={dry}, "
                    f"keep-married-from-domacinstvo={keep_from_dom}) ==="
                )
            )
            with tenant_context(zakupac):
                self._popravi(dry_run=dry, keep_from_dom=keep_from_dom)

    # ------------------------------------------------------------------ #
    def _popravi(self, dry_run: bool, keep_from_dom: bool) -> None:
        # Хвата све чије prezime почиње препознатим маркером. Ради се
        # кроз Python (не SQL ILIKE) јер regex има више варијанти, а
        # желимо да izdvoj_devojacko буде једини извор истине.
        candidates = list(
            Osoba.objects.exclude(prezime__isnull=True)
            .exclude(prezime__exact="")
            .iterator()
        )

        affected = 0
        skipped_no_marker = 0
        married_from_dom = 0
        for o in candidates:
            _, devojacko = izdvoj_devojacko(o.prezime)
            if not devojacko:
                skipped_no_marker += 1
                continue

            novo_devojacko = o.devojacko or devojacko
            novo_prezime = ""  # подразумевано празно — службеник попуњава

            if keep_from_dom:
                inferred = self._infer_married_from_domacinstvo(o)
                if inferred:
                    novo_prezime = inferred
                    married_from_dom += 1

            affected += 1
            self.stdout.write(
                f"  uid={o.uid} {o.ime!r}: "
                f"prezime {o.prezime!r} -> {novo_prezime!r}, "
                f"devojacko {o.devojacko!r} -> {novo_devojacko!r}"
            )
            if dry_run:
                continue
            with transaction.atomic():
                Osoba.objects.filter(pk=o.pk).update(
                    prezime=novo_prezime,
                    devojacko=novo_devojacko,
                )

        verb = "Препознато" if dry_run else "Поправљено"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {affected} Osoba (без маркера: {skipped_no_marker}, "
                f"из домаћинства преузето удато презиме: {married_from_dom})."
            )
        )

    # ------------------------------------------------------------------ #
    def _infer_married_from_domacinstvo(self, osoba: Osoba) -> str:
        """Return a probable married surname for ``osoba`` from her household.

        Logic (best-effort, conservative):
          1. If she IS a domaćin of a Domaćinstvo: we have nothing better
             than her own (now-blank) prezime → return "".
          2. Otherwise look up Ukucanin rows for this Osoba and use the
             linked Domaćinstvo's domaćin.prezime, IF that prezime is
             non-blank AND has no marker.
        """
        # случај (1)
        if Domacinstvo.objects.filter(domacin=osoba).exists():
            return ""
        # случај (2)
        for u in Ukucanin.objects.filter(osoba=osoba).select_related(
            "domacinstvo__domacin"
        ):
            d = u.domacinstvo
            if not d or not d.domacin_id:
                continue
            host_prez = (d.domacin.prezime or "").strip()
            if not host_prez:
                continue
            host_married, host_devojacko = izdvoj_devojacko(host_prez)
            if host_devojacko:  # домаћин и сам има маркер — прескочи
                continue
            return host_married
        return ""
