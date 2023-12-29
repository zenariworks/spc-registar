from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Покреће више команди заједно'

    def handle(self, *args, **kwargs):
        # Списак команди које треба извршити
        commands = [
            ('unos_dana', {}),
            ('unos_meseci', {}),
            ('unos_narodnosti', {}),
            ('unos_veroispovesti', {}),
            ('unos_zanimanja', {}),
            ('unos_slava', {}),
        ]

        for command_name, command_kwargs in commands:
            try:
                self.stdout.write(f"Извршење команде: {command_name}")
                call_command(command_name, **command_kwargs)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Грешка при извршењу {command_name}: {e}"))

        self.stdout.write(self.style.SUCCESS('Успешно извршене све команде у групи.'))
