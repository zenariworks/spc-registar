"""Django management command to mark major feast days (crveno slovo)."""

from django.core.management.base import BaseCommand
from registar.models import Slava


class Command(BaseCommand):
    help = 'Mark major Orthodox feast days as "crveno slovo" (red letter days)'

    def handle(self, *args, **options):
        # Major feast days that should be marked as "crveno slovo"
        major_feasts = [
            # Велики Господњи празници (Great Feasts of the Lord)
            "Божић",
            "Богојављење",
            "Благовести",
            "Улазак Господа Исуса Христа у Јерусалим",  # Palm Sunday
            "Велики четвртак (Велико бденије)",
            "Велики петак",
            "Велика субота",
            "Васкрсење Господа исуса Христа",  # Easter - most important
            "Вазнесење Господње",
            "Силазак Светог Духа на апостоле-Педесетница-Тројице",  # Pentecost
            "Велика Госпојина",  # Dormition
            "Мала Госпојина",  # Nativity of Theotokos
            "Ваведење",  # Presentation of Mary
            # Велики светитељски празници (Great Feasts of Saints)
            "Свети Сава",
            "Свети Никола",
            "Ђурђевдан",  # Saint George
        ]

        updated_count = 0
        for feast_name in major_feasts:
            try:
                # Try exact match first
                slava = Slava.objects.filter(naziv__icontains=feast_name).first()

                if slava:
                    old_value = slava.crveno_slovo
                    slava.crveno_slovo = True
                    slava.save()

                    status = "already marked" if old_value else "marked"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ {slava.naziv} - {status} as crveno slovo"
                        )
                    )
                    if not old_value:
                        updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ "{feast_name}" not found in database')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error processing {feast_name}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nMarked {updated_count} new feast(s) as crveno slovo")
        )

        # Show all red letter days
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("All Red Letter Days (Црвено слово):")
        self.stdout.write("=" * 70)
        red_letter_days = Slava.objects.filter(crveno_slovo=True).order_by(
            "mesec", "dan"
        )
        for slava in red_letter_days:
            if slava.pokretni:
                date_2025 = slava.get_datum(2025)
                date_str = date_2025.strftime("%B %d")
                self.stdout.write(f"  {slava.naziv} (moveable, 2025: {date_str})")
            else:
                self.stdout.write(f"  {slava.naziv} ({slava.mesec}/{slava.dan})")
