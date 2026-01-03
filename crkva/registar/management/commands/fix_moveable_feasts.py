"""Django management command to fix moveable feasts in the database."""

from django.core.management.base import BaseCommand
from registar.models import Slava


class Command(BaseCommand):
    help = "Convert Easter and related feasts from fixed to moveable dates"

    def handle(self, *args, **options):
        # Easter-related feasts that should be moveable
        # Offset is calculated from Easter Sunday
        easter_feasts = [
            {
                "name": "Лазарева субота",
                "offset_days": -8,  # Saturday before Palm Sunday
                "offset_weeks": 0,
            },
            {
                "name": "Улазак Господа Исуса Христа у Јерусалим",
                "offset_days": -7,  # Palm Sunday (Sunday before Easter)
                "offset_weeks": 0,
            },
            {
                "name": "Велики четвртак (Велико бденије)",
                "offset_days": -3,  # Holy Thursday (Maundy Thursday)
                "offset_weeks": 0,
            },
            {
                "name": "Велики петак",
                "offset_days": -2,  # Good Friday
                "offset_weeks": 0,
            },
            {
                "name": "Велика субота",
                "offset_days": -1,  # Holy Saturday
                "offset_weeks": 0,
            },
            {
                "name": "Васкрсење Господа исуса Христа",
                "offset_days": 0,  # Easter Sunday
                "offset_weeks": 0,
            },
            {
                "name": "Васкрски понедељак",
                "offset_days": 1,  # Easter Monday (Bright Monday)
                "offset_weeks": 0,
            },
            {
                "name": "Васкрсни уторак",
                "offset_days": 2,  # Easter Tuesday (Bright Tuesday)
                "offset_weeks": 0,
            },
            {
                "name": "Вазнесење Господње",
                "offset_days": 39,  # Ascension (40th day from Easter)
                "offset_weeks": 0,
            },
            {
                "name": "Силазак Светог Духа на апостоле-Педесетница-Тројице",
                "offset_days": 49,  # Pentecost/Trinity (50th day from Easter)
                "offset_weeks": 0,
            },
            {
                "name": "Духовски понедељак",
                "offset_days": 50,  # Pentecost Monday
                "offset_weeks": 0,
            },
            {
                "name": "Духовски уторак",
                "offset_days": 51,  # Pentecost Tuesday
                "offset_weeks": 0,
            },
        ]

        updated_count = 0
        for feast in easter_feasts:
            try:
                slava = Slava.objects.get(naziv=feast["name"])
                old_date = (
                    f"{slava.mesec}/{slava.dan}"
                    if slava.mesec and slava.dan
                    else "moveable"
                )

                slava.pokretni = True
                slava.offset_dani = feast["offset_days"]
                slava.offset_nedelje = feast["offset_weeks"]
                slava.dan = None
                slava.mesec = None
                slava.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Updated {feast["name"]} (was {old_date}) to moveable feast'
                    )
                )
                updated_count += 1
            except Slava.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Feast "{feast["name"]}" not found in database'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error updating {feast["name"]}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nUpdated {updated_count} feast(s) to moveable dates")
        )

        # Verify the changes
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("Verification - Dates for 2025 and 2026:")
        self.stdout.write("=" * 70)
        for feast in easter_feasts:
            try:
                slava = Slava.objects.get(naziv=feast["name"])
                date_2025 = slava.get_datum(2025)
                date_2026 = slava.get_datum(2026)
                self.stdout.write(f'\n{feast["name"]}:')
                self.stdout.write(f'  2025: {date_2025.strftime("%B %d, %Y")}')
                self.stdout.write(f'  2026: {date_2026.strftime("%B %d, %Y")}')
            except Slava.DoesNotExist:
                pass
