"""Помирење покретних празника Васкршњег циклуса (issue #259).

Идемпотентно и самочистеће. За сваки празник из канонског списка
``kalendar.feasts.MOVEABLE_FEASTS``:

1. осигурава тачно један **покретни** ред (``upsert_moveable_feasts``), и
2. брише евентуалне вишак фиксне копије истог празника — претходно
   премештајући ``Domacinstvo`` везе на канонски ред.

Те вишак фиксне копије настајале су јер сејачи (``migracija_slava`` /
``unos_slava``) уписиваху покретне празнике као фиксне. Од issue #259 сејачи
користе исти канонски списак и **не** праве фиксне копије, па ова команда
првенствено служи помирењу већ постојећих база и као последњи корак у
``importuj_dbf``.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django_tenants.utils import get_tenant_model, schema_context

from kalendar.feasts import MOVEABLE_FEASTS, upsert_moveable_feasts
from kalendar.models import Slava


class Command(BaseCommand):
    help = "Осигурај покретне празнике Васкршњег циклуса и обриши фиксне дупликате"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Само прикажи шта би било промењено/обрисано, без уписа у базу.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            for feast in MOVEABLE_FEASTS:
                rows = list(
                    Slava.objects.filter(naziv=feast["naziv"]).order_by("uid")
                )
                if not rows:
                    self.stdout.write(
                        f'• {feast["naziv"]}: недостаје → биће креиран као покретни'
                    )
                    continue
                canonical = next((r for r in rows if r.pokretni), rows[0])
                dupes = [r.uid for r in rows if r.uid != canonical.uid]
                self.stdout.write(
                    f'• {feast["naziv"]}: канонски uid={canonical.uid}'
                    + (f", за брисање: {dupes}" if dupes else " (нема дупликата)")
                )
            self.stdout.write(self.style.NOTICE("\n(dry-run — ништа није уписано)"))
            return

        deleted = 0
        with transaction.atomic():
            # 1) осигурај тачно један покретни ред по празнику (исти извор
            #    истине који користе и сејачи).
            upsert_moveable_feasts(stdout=self.stdout)

            # 2) обриши вишак фиксних копија, премештајући везе на канонски ред.
            for feast in MOVEABLE_FEASTS:
                rows = list(
                    Slava.objects.filter(naziv=feast["naziv"]).order_by("uid")
                )
                canonical = next(r for r in rows if r.pokretni)
                for dup in rows:
                    if dup.uid == canonical.uid:
                        continue
                    moved = self._reassign_households(dup.uid, canonical.uid)
                    self._delete_slava(dup.uid)
                    deleted += 1
                    note = f" (премештено {moved} домаћинстава)" if moved else ""
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ✗ обрисан вишак uid={dup.uid} за „{feast['naziv']}“{note}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nОсигурано покретних: {len(MOVEABLE_FEASTS)}; обрисано дупликата: {deleted}"
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
