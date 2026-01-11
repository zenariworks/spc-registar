"""
Migracija табеле укућана из PostgreSQL staging табеле 'hsp_ukucani' у модел Ukucanin.
Ова миграција се извршава прва, јер друге миграције могу зависити од парохијана.
"""

from typing import Iterable

from django.db import connection
from registar.management.commands.base_migration import MigrationCommand
from registar.management.commands.convert_utils import Konvertor
from registar.models import Parohijan, Ukucanin


class Command(MigrationCommand):
    help = "Migracija табеле укућана из staging табеле 'hsp_ukucani'"

    staging_table = "hsp_ukucani"
    target_model = Ukucanin

    def handle(self, *args, **kwargs) -> None:
        self.clear_target_table()
        self.stdout.write(
            f"Учитавам податке из staging табеле '{self.staging_table}'..."
        )

        records = self._parse_and_prepare_records()
        created_count = self.migrate_in_batches(records)

        self.log_success(created_count, table_name="укућани")
        self.drop_staging_table()

    def _parse_and_prepare_records(self) -> Iterable[dict | None]:
        """
        Чита податке из staging табеле и припрема их за bulk_create.
        Враћа generator диктова (или None ако запис треба прескочити).
        """
        # Предкеширај све парохијане по uid-у за O(1) приступ
        parohijani_cache = {p.uid: p for p in Parohijan.objects.all()}

        query = 'SELECT "UK_RBRDOM", "UK_IME" FROM hsp_ukucani ORDER BY "UK_RBRDOM"'

        with connection.cursor() as cursor:
            cursor.execute(query)
            for row in cursor.fetchall():
                raw_uid, raw_ime = row

                uid = int(raw_uid) if raw_uid else 0
                ime = Konvertor.string(raw_ime or "").strip()

                if uid == 0 or uid not in parohijani_cache:
                    self.log_skip(f"Парохијан са UID {uid} не постоји")
                    yield None
                    continue

                if not ime:
                    self.log_skip(f"Празно име укућанина за парохијана UID {uid}")
                    yield None
                    continue

                yield {
                    "parohijan": parohijani_cache[uid],
                    "ime_ukucana": ime,
                }
