"""Миграција парохијана — преусмерава на migracija_ukucana_parohijana."""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Миграција парохијана (преусмерава на migracija_ukucana_parohijana)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Преусмерава на migracija_ukucana_parohijana...")
        call_command("migracija_ukucana_parohijana")
