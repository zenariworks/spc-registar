"""Post-hoc cleanup: split ``р.<X>`` / ``рођ.<X>`` / ``r.<X>`` surname
prefixes into ``devojacko_prezime``.

The DBF import historically glued the maiden-name marker onto the
``prezime`` field — e.g. ``"Татјана р.Бошковић"`` became
``ime="Татјана", prezime="р.Бошковић"`` instead of
``prezime="", devojacko_prezime="Бошковић"``. The ``р.`` is Serbian
shorthand for "рођена" (née / maiden surname).

This command finds those rows and moves the maiden part to
``devojacko_prezime``. The married surname is NOT recorded in the source
DBF — by default we leave ``prezime`` blank so a clerk can fill it in.
With ``--keep-married-from-domacinstvo`` we attempt to infer the married
surname from a Domaćinstvo whose domaćin is a different Osoba with a
non-prefixed prezime.

Usage:
  manage.py popravi_devojacka --dry-run
  manage.py popravi_devojacka --schema crkva_sv_petke_cukarica
  manage.py popravi_devojacka --keep-married-from-domacinstvo
"""

# pylint: disable=missing-function-docstring,missing-class-docstring,too-many-locals,broad-exception-caught,import-outside-toplevel

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from registar.migracija.helpers import extract_maiden
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
        only_schema: str | None = opts.get("schema")
        keep_from_dom: bool = opts["keep_married_from_domacinstvo"]

        for t in tenant_model.objects.exclude(schema_name="public"):
            if only_schema and t.schema_name != only_schema:
                continue
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"\n=== {t.schema_name} (dry-run={dry}, "
                    f"keep-married-from-domacinstvo={keep_from_dom}) ==="
                )
            )
            with tenant_context(t):
                self._popravi(dry_run=dry, keep_from_dom=keep_from_dom)

    # ------------------------------------------------------------------ #
    def _popravi(self, dry_run: bool, keep_from_dom: bool) -> None:
        # Match anything whose prezime starts with a recognised marker.
        # Done via Python (not SQL ILIKE) because the regex has several
        # variants and we want extract_maiden to be the single source of
        # truth.
        candidates = list(
            Osoba.objects.exclude(prezime__isnull=True)
            .exclude(prezime__exact="")
            .iterator()
        )

        affected = 0
        skipped_no_marker = 0
        married_from_dom = 0
        for o in candidates:
            _, maiden = extract_maiden(o.prezime)
            if not maiden:
                skipped_no_marker += 1
                continue

            new_devojacko = o.devojacko_prezime or maiden
            new_prezime = ""  # default: blank — clerk fills in

            if keep_from_dom:
                inferred = self._infer_married_from_domacinstvo(o)
                if inferred:
                    new_prezime = inferred
                    married_from_dom += 1

            affected += 1
            self.stdout.write(
                f"  uid={o.uid} {o.ime!r}: "
                f"prezime {o.prezime!r} -> {new_prezime!r}, "
                f"devojacko {o.devojacko_prezime!r} -> {new_devojacko!r}"
            )
            if dry_run:
                continue
            with transaction.atomic():
                Osoba.objects.filter(pk=o.pk).update(
                    prezime=new_prezime,
                    devojacko_prezime=new_devojacko,
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
        # case (1)
        if Domacinstvo.objects.filter(domacin=osoba).exists():
            return ""
        # case (2)
        for u in Ukucanin.objects.filter(osoba=osoba).select_related(
            "domacinstvo__domacin"
        ):
            d = u.domacinstvo
            if not d or not d.domacin_id:
                continue
            host_prez = (d.domacin.prezime or "").strip()
            if not host_prez:
                continue
            host_married, host_maiden = extract_maiden(host_prez)
            if host_maiden:  # host itself still has a marker — skip
                continue
            return host_married
        return ""
