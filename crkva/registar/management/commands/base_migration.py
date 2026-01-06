"""
Базна класа за миграционе команде.

Садржи заједничку логику за све миграционе команде које користе staging табеле.
"""

import re

from django.core.management.base import BaseCommand
from django.db import connection


class MigrationCommand(BaseCommand):
    """
    Апстрактна базна класа за миграционе команде.

    Пружа заједничку функционалност:
    - Брисање staging табеле након миграције
    - Брисање постојећих података пре миграције
    - Стандардни формат исписа успеха/грешке
    """

    # Подкласе морају да дефинишу ове атрибуте
    staging_table_name = None  # Име staging табеле (нпр. 'hsp_krstenja')
    target_model = None  # Django модел у који се мигрира

    def drop_staging_table(self):
        """Брише staging табелу након успешне миграције."""
        if not self.staging_table_name:
            raise NotImplementedError(
                "staging_table_name мора бити дефинисан у подкласи"
            )

        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {self.staging_table_name}")
        self.stdout.write(
            self.style.SUCCESS(f"Обрисана staging табела '{self.staging_table_name}'.")
        )

    def clear_target_table(self):
        """Брише све податке из циљне табеле пре миграције."""
        if not self.target_model:
            raise NotImplementedError("target_model мора бити дефинисан у подкласи")

        self.target_model.objects.all().delete()

    def log_success(self, count, table_name=None):
        """Исписује поруку о успешној миграцији."""
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

    def log_error(self, message):
        """Исписује поруку о грешци."""
        self.stdout.write(self.style.ERROR(f"Грешка при креирању уноса: {message}"))

    def log_warning(self, message):
        """Исписује упозорење."""
        self.stdout.write(self.style.WARNING(message))

    def log_skip(self, reason):
        """Исписује поруку о прескоченом запису."""
        self.stdout.write(self.style.WARNING(f"Прескочено: {reason}"))

    def split_full_name(self, full_name):
        """
        Раздваја пуно име на име и презиме.

        Покушава:
        1. Раздвајање по размаку (стандардно)
        2. Раздвајање по великом ћириличном слову у средини речи
           (за случајеве као "СлавицаЋуковић" → "Славица", "Ћуковић")

        Args:
            full_name: Пуно име као стринг

        Returns:
            tuple: (име, презиме) или (None, None) ако не може да раздвоји
        """
        if not full_name:
            return None, None

        full_name = full_name.strip()
        if not full_name:
            return None, None

        # Покушај стандардно раздвајање по размаку
        if " " in full_name:
            parts = full_name.split(maxsplit=1)
            if len(parts) == 2:
                return parts[0], parts[1]

        # Покушај раздвајање по великом ћириличном слову у средини речи
        # Ћирилична велика слова: А-Я, Ђ, Ј, Љ, Њ, Ћ, Џ
        match = re.match(
            r"^([А-ЯЂЈЉЊЋЏа-яђјљњћџ]+?)([А-ЯЂЈЉЊЋЏ][а-яђјљњћџ]+)$", full_name
        )
        if match:
            return match.group(1), match.group(2)

        return None, None
