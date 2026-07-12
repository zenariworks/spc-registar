"""Попуњава табелу Слава из ``fixtures/slave.jsonl``.

JSONL је јединствени извор празника (issue #259): сваки ред носи изричита
поља — ``naziv``, ``opsti_naziv``, ``dan``, ``mesec``, ``pokretni``,
``offset_dani``, ``crveno_slovo`` — па се и фиксни и покретни празници сеју из
истог фајла, без накнадне конверзије. Идемпотентно (``update_or_create``).
"""

import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from kalendar.models import Slava

FIXTURE = os.path.join(settings.BASE_DIR, "fixtures", "slave.jsonl")


class Command(BaseCommand):
    help = "Попуњава табелу Слава из fixtures/slave.jsonl (фиксни и покретни празници)."

    def handle(self, *args, **kwargs):
        created = updated = 0
        for row in self._parse_data():
            try:
                if row["pokretni"]:
                    # Покретни празник: кључ је назив (међу покретнима
                    # јединствен), датум празан, помак од Васкрса.
                    _, was_created = Slava.objects.update_or_create(
                        naziv=row["naziv"],
                        pokretni=True,
                        defaults={
                            "opsti_naziv": row.get("opsti_naziv", ""),
                            "dan": None,
                            "mesec": None,
                            "offset_dani": row.get("offset_dani"),
                            "offset_nedelje": 0,
                            "crveno_slovo": row.get("crveno_slovo", False),
                        },
                    )
                else:
                    # Фиксни празник: кључ је (назив, дан, месец) — дозвољава
                    # легитимне истоимене празнике на различите дане.
                    _, was_created = Slava.objects.update_or_create(
                        naziv=row["naziv"],
                        dan=row["dan"],
                        mesec=row["mesec"],
                        defaults={
                            "opsti_naziv": row.get("opsti_naziv", ""),
                            "pokretni": False,
                            "offset_dani": None,
                            "offset_nedelje": None,
                            "crveno_slovo": row.get("crveno_slovo", False),
                        },
                    )
                created += int(was_created)
                updated += int(not was_created)
            except IntegrityError as e:
                self.stdout.write(
                    self.style.ERROR(f"Грешка при упису „{row.get('naziv')}“: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Слава засејана из slave.jsonl: {created} нових, {updated} ажурираних."
            )
        )

    @staticmethod
    def _parse_data():
        """Чита ``fixtures/slave.jsonl`` (по један JSON објекат у реду)."""
        rows = []
        with open(FIXTURE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
