"""Django management command to fix moveable feasts in the database.

Idempotent and self-healing (see issue #259). For each Paschal-cycle feast it:

1. converts a single *canonical* Slava row to a moveable feast — ``pokretni``
   with an offset from Pascha and ``dan``/``mesec`` cleared, and
2. removes any leftover *fixed* duplicate rows of the same feast, after
   repointing any household (``Domacinstvo``) references to the canonical row.

Those stray fixed copies (e.g. uid 366–377 on production) are recreated every
time the seeding commands (``migracija_slava`` / ``unos_slava``) run, because
they key ``get_or_create`` on ``(naziv, dan, mesec)`` and therefore never match
an already-converted moveable row whose ``dan``/``mesec`` are NULL. Re-running
this command after a re-seed cleans them up again.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django_tenants.utils import get_tenant_model, schema_context

from kalendar.models import Slava

# Празници Васкршњег циклуса. Помак (offset) се рачуна од Васкрсне недеље.
EASTER_FEASTS = [
    {"name": "Лазарева субота", "offset_days": -8, "offset_weeks": 0},
    {"name": "Улазак Господа Исуса Христа у Јерусалим", "offset_days": -7, "offset_weeks": 0},
    {"name": "Велики четвртак (Велико бденије)", "offset_days": -3, "offset_weeks": 0},
    {"name": "Велики петак", "offset_days": -2, "offset_weeks": 0},
    {"name": "Велика субота", "offset_days": -1, "offset_weeks": 0},
    {"name": "Васкрсење Господа исуса Христа", "offset_days": 0, "offset_weeks": 0},
    {"name": "Васкрски понедељак", "offset_days": 1, "offset_weeks": 0},
    {"name": "Васкрсни уторак", "offset_days": 2, "offset_weeks": 0},
    {"name": "Вазнесење Господње", "offset_days": 39, "offset_weeks": 0},
    {"name": "Силазак Светог Духа на апостоле-Педесетница-Тројице", "offset_days": 49, "offset_weeks": 0},
    {"name": "Духовски понедељак", "offset_days": 50, "offset_weeks": 0},
    {"name": "Духовски уторак", "offset_days": 51, "offset_weeks": 0},
]


class Command(BaseCommand):
    help = "Convert Easter-cycle feasts to moveable dates and prune fixed duplicates"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Само прикажи шта би било промењено/обрисано, без уписа у базу.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        converted = 0
        deleted = 0

        for feast in EASTER_FEASTS:
            rows = list(Slava.objects.filter(naziv=feast["name"]).order_by("uid"))
            if not rows:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Празник „{feast["name"]}“ није пронађен')
                )
                continue

            # Канонски ред: већ покретни ако постоји, иначе најмањи uid.
            canonical = next((r for r in rows if r.pokretni), rows[0])
            duplicates = [r for r in rows if r.uid != canonical.uid]

            if dry_run:
                self.stdout.write(
                    f'• {feast["name"]}: канонски uid={canonical.uid}'
                    + (
                        f", за брисање: {[d.uid for d in duplicates]}"
                        if duplicates
                        else " (нема дупликата)"
                    )
                )
                continue

            with transaction.atomic():
                canonical.pokretni = True
                canonical.offset_dani = feast["offset_days"]
                canonical.offset_nedelje = feast["offset_weeks"]
                canonical.dan = None
                canonical.mesec = None
                canonical.save()
                converted += 1

                for dup in duplicates:
                    moved = self._reassign_households(dup.uid, canonical.uid)
                    dup_uid = dup.uid
                    self._delete_slava(dup_uid)
                    deleted += 1
                    note = f" (премештено {moved} домаћинстава)" if moved else ""
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ✗ обрисан вишак uid={dup_uid} за „{feast['name']}“{note}"
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ „{feast["name"]}“ → покретни (uid={canonical.uid})'
                )
            )

        if dry_run:
            self.stdout.write(self.style.NOTICE("\n(dry-run — ништа није уписано)"))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"\nПретворено покретних: {converted}; обрисано дупликата: {deleted}"
            )
        )

    @staticmethod
    def _delete_slava(uid):
        """Брише ред из public ``slave`` сировим SQL-ом.

        ``Slava`` је shared (public) модел, а њен reverse FK (tenant
        ``Domacinstvo.slava``, ``db_constraint=False``) натера Django
        collector да при ``.delete()`` дира tenant табелу у public шеми
        (које тамо нема). Везе су већ премештене у
        :meth:`_reassign_households`, па бришемо директно, без ORM
        collector-а.
        """
        with schema_context("public"):
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM slave WHERE uid = %s", [uid])

    def _reassign_households(self, old_uid, new_uid):
        """Премешта tenant ``Domacinstvo`` везе са вишка славе на канонску, у свим шемама.

        ``Slava`` је у public шеми, а ``Domacinstvo`` је tenant табела са
        cross-schema FK (``db_constraint=False``), па морамо проћи кроз сваку
        tenant шему појединачно.
        """
        from registar.models import Domacinstvo

        tenant_model = get_tenant_model()
        moved = 0
        for tenant in tenant_model.objects.exclude(schema_name="public"):
            with schema_context(tenant.schema_name):
                moved += Domacinstvo.objects.filter(slava_id=old_uid).update(
                    slava_id=new_uid
                )
        return moved
