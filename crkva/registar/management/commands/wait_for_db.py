"""Модул Ђанго команде за чекање постојеће базе података."""

import time

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg2 import OperationalError as Psycopg2OpError


class Command(BaseCommand):
    """Класа Ђанго команде за чекање постојеће базе података."""

    def handle(self, *args, **options):
        """Почетна тачка команде."""
        self.stdout.write("Чекање на базу података...")
        db_up = False
        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True
            except (Psycopg2OpError, OperationalError):
                self.stdout.write("База података недоступна, чекам 1 секунд...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("База података је доступна!"))
