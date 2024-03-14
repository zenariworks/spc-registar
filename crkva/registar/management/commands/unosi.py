from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
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
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Грешка при извршењу {kommanda}: {e}")
                )

        self.stdout.write(self.style.SUCCESS("Успешно извршене све команде у групи."))
