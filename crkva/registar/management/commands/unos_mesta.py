"""
Модул команде за унос места без повезивања са општинама.
"""

import random

from django.core.management.base import BaseCommand
from registar.models import Mesto

mesta = [
    "Место 1",
    "Место 2",
    "Место 3",
    "Место 4",
    "Место 5",
    # ...
]


def unesi_mesto(naziv: str | Mesto | None = None) -> tuple[Mesto, bool]:
    """
    Уноси ново место у базу података или враћа постојеће.

    :param naziv: Назив места или објекат места
    :return: Креирано или постојеће место и флаг да ли је креирано ново
    """
    if isinstance(naziv, Mesto):
        return naziv, False
    naziv = naziv or random.choice(mesta)
    mesto, uneto = Mesto.objects.get_or_create(naziv=naziv)
    return mesto, uneto


class Command(BaseCommand):
    """
    Класа Ђанго команде за унос места без повезивања са општинама.
    """

    help = "Унос места без повезивања са општинама"

    def handle(self, *args, **kwargs):
        for naziv in mesta:
            mesto, uneto = unesi_mesto(naziv)
            if uneto:
                info = f"Додато место `{mesto}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Место `{mesto}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
