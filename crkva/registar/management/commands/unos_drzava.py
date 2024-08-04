"""
Модул за унос држава и њихово повезивање са базом података.
"""

import random

from django.core.management.base import BaseCommand
from registar.models import Drzava

drzave = {
    ("Србија", "Srbija"): r"^\d{5}$",
    ("Босна и Херцеговина", "Bosna i Hercegovina"): r"^\d{5}$",
    ("Црна Гора", "Crna Gora"): r"^\d{5}$",
    ("Хрватска", "Hrvatska"): r"^\d{5}$",
    ("Северна Македонија", "Северна Македонија"): r"^\d{4}$",
    ("Сједињене Америчке Државе", "United States"): r"^\d{5}(-\d{4})?$",
    ("Канада", "Canada"): r"^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$",
    ("Аустралија", "Australia"): r"^\d{4}$",
    ("Нови Зеланд", "New Zealand"): r"^\d{4}$",
    ("Немачка", "Deutschland"): r"^\d{5}$",
    ("Аустрија", "Österreich"): r"^\d{4}$",
    ("Швајцарска", "Schweiz"): r"^\d{4}$",
    ("Француска", "France"): r"^\d{5}$",
    ("Шведска", "Sverige"): r"^\d{3} \d{2}$",
    ("Норвешка", "Norge"): r"^\d{4}$",
    ("Данска", "Danmark"): r"^\d{4}$",
    ("Холандија", "Nederland"): r"^\d{4} [A-Z]{2}$",
    ("Белгија", "België"): r"^\d{4}$",
}


def unesi_drzavu(naziv: str | Drzava | None = None) -> tuple[Drzava, bool]:
    """
    Уноси државу у базу података или враћа постојећу.

    :param naziv: Назив државе или објекат државе
    :return: Креирана или постојећа држава и флаг да ли је креирана нова
    """
    if isinstance(naziv, Drzava):
        return naziv, False

    for (srpski, izvorni), regex in drzave.items():
        if naziv in [srpski, izvorni]:
            return Drzava.objects.get_or_create(
                naziv=srpski,
                defaults={"postkod_regex": regex, "izvorni_naziv": izvorni},
            )

    drzava = Drzava.objects.order_by("?").first()
    if not drzava:
        (srpski, izvorni), regex = random.choice(list(drzave.items()))
        drzava, uneto = Drzava.objects.get_or_create(
            naziv=srpski,
            defaults={"postkod_regex": regex, "izvorni_naziv": izvorni},
        )
        return drzava, uneto

    return drzava, False


class Command(BaseCommand):
    """
    Класа Ђанго команде за унос држава, ако већ нису у бази података.
    """

    help = "Унос држава, ако већ нису у бази података"

    def handle(self, *args, **kwargs):
        for naziv, _ in drzave.keys():
            drzava, uneto = unesi_drzavu(naziv)
            if uneto:
                info = f"Додата држава `{drzava}`"
                self.stdout.write(self.style.SUCCESS(info))
            else:
                info = f"Држава `{drzava}` већ постоји."
                self.stdout.write(self.style.WARNING(info))
