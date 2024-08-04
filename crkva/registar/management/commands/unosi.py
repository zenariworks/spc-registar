"""
Модул команде за покретање више команди заједно.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Класа Ђанго команде за покретање више команди заједно.
    """

    help = "Покреће више команди заједно"

    def handle(self, *args, **kwargs):
        # Списак команди које треба извршити
        komande = [
            ("unos_dana", {}),
            ("unos_meseci", {}),
            ("unos_narodnosti", {}),
            ("unos_veroispovesti", {}),
            ("unos_zanimanja", {}),
            ("unos_slava", {}),
            ("unos_eparhija", {}),
        ]

        for kommanda, command_kwargs in komande:
            try:
                self.stdout.write(f"Извршење команде: {kommanda}")
                call_command(kommanda, **command_kwargs)
            except CommandError as ce:
                self.stdout.write(
                    self.style.ERROR(f"Командна грешка при извршењу {kommanda}: {ce}")
                )
            except FileNotFoundError as fnfe:
                self.stdout.write(
                    self.style.ERROR(
                        f"Датотека није пронађена при извршењу {kommanda}: {fnfe}"
                    )
                )
            except IOError as ioe:
                self.stdout.write(
                    self.style.ERROR(f"ИО грешка при извршењу {kommanda}: {ioe}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Непозната грешка при извршењу {kommanda}: {e}")
                )

        self.stdout.write(self.style.SUCCESS("Успешно извршене све команде у групи."))
