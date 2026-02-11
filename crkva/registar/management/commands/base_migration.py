"""
Базна класа за миграционе команде.

Садржи заједничку логику за све миграционе команде које користе staging табеле.
"""

import re
from typing import Iterable

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.transaction import atomic
from registar.models import Osoba


class MigrationCommand(BaseCommand):
    """
    Апстрактна базна класа за миграционе команде.

    Пружа заједничку функционалност:
    - Брисање staging табеле након миграције
    - Брисање постојећих података пре миграције
    - Стандардни формат исписа успеха/грешке
    - bulk_create у батчевима са прогресом
    - get_or_create логика за особе
    """

    staging_table: str | None = None
    target_model = None

    def drop_staging_table(self) -> None:
        """Брише staging табелу након успешне миграције."""
        if not (table := self.staging_table):
            raise NotImplementedError("staging_table мора бити дефинисан у подкласи")

        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

        self.stdout.write(self.style.SUCCESS(f"Обрисана staging табела '{table}'."))

    def clear_target_table(self) -> None:
        """Брише све податке из циљне табеле пре миграције."""
        if not self.target_model:
            raise NotImplementedError("target_model мора бити дефинисан у подкласи")

        self.target_model.objects.all().delete()

    def log_success(self, count: int, table_name: str | None = None) -> None:
        name = table_name or (
            self.target_model._meta.verbose_name_plural
            if self.target_model
            else "записа"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно попуњена табела '{name}': {count} нових уноса."
            )
        )

    def log_error(self, message: str) -> None:
        self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {message}"))

    def log_warning(self, message: str) -> None:
        self.stdout.write(self.style.WARNING(message))

    def log_skip(self, reason: str) -> None:
        self.stdout.write(self.style.WARNING(f"Прескочено: {reason}"))

    def split_full_name(self, full_name: str | None) -> tuple[str | None, str | None]:
        """
        Раздваја пуно име на име и презиме (подржава спојена имена попут "СлавицаЋуковић").
        """
        if not full_name or not (full_name := full_name.strip()):
            return None, None

        # 1. Стандардно по размаку
        if " " in full_name:
            first, last = full_name.split(maxsplit=1)
            return first, last

        # 2. По великом слову у средини (ћирилично)
        if match := re.match(
            r"^([А-ЯЂЈЉЊЋЏа-яђјљњћџ]+?)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)$", full_name
        ):
            return match.group(1), match.group(2)

        return None, None

    def get_or_create_osoba(self, ime: str, prezime: str, **extra) -> Osoba | None:
        """
        Проналази или креира особу. Ажурира празна поља ако особа већ постоји.
        """
        if not (ime := ime.strip()) or not (prezime := prezime.strip()):
            return None

        if osoba := Osoba.objects.filter(
            ime__iexact=ime, prezime__iexact=prezime
        ).first():
            updates = {
                k: v
                for k, v in extra.items()
                if v and getattr(osoba, k, None) in (None, "", False)
            }
            if updates:
                Osoba.objects.filter(pk=osoba.pk).update(**updates)
            return osoba

        create_data = {
            "ime": ime,
            "prezime": prezime,
            "parohijan": False,
            **{k: v for k, v in extra.items() if v is not None},
        }
        return Osoba.objects.create(**create_data)

    @atomic
    def migrate_in_batches(
        self, records: Iterable[dict | None], batch_size: int = 500
    ) -> int:
        """
        Мигрира записе у батчевима користећи bulk_create.
        Прескаче None записе. Враћа број успешно додатих записа.
        """
        batch: list = []
        created_count = 0

        for idx, data in enumerate(records, start=1):
            if data is None:
                continue

            batch.append(self.target_model(**data))
            created_count += 1

            if len(batch) >= batch_size:
                self.target_model.objects.bulk_create(batch, ignore_conflicts=True)
                batch.clear()
                self.stdout.write(f"Обрађено {idx} записа...")

        if batch:
            self.target_model.objects.bulk_create(batch, ignore_conflicts=True)

        return created_count
