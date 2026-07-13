"""Регресија за #335: велики празници морају носити `crveno_slovo=true`.

Стара `mark_major_feasts` команда је означавала црвена слова преко
`naziv__icontains` над народним именима — па Божић, Богојављење, обе
Госпојине и Ђурђевдан никад нису добили црвено. Команда је уклоњена
(#299/#323): црвено слово сада иде директно из фикстуре `slave.jsonl`,
која мора имати тачне вредности.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

import io
import json
import os

from django.conf import settings
from django.test import SimpleTestCase

JSONL = os.path.join(settings.BASE_DIR, "fixtures", "slave.jsonl")

# (dan, mesec) великих празника — сви морају бити црвено слово (грегоријански).
CRVENA_SLOVA = [
    (7, 1),  # Божић (Рождество Христово)
    (19, 1),  # Богојављење
    (6, 5),  # Ђурђевдан (Свети великомученик Георгије)
    (28, 8),  # Успење (Велика Госпојина)
    (21, 9),  # Мала Госпојина (Рођење Богородице)
    (4, 12),  # Ваведење
]


class CrvenoSlovoFixtureTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.by_date = {}
        with io.open(JSONL, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if not r["pokretni"]:
                    cls.by_date[(r["dan"], r["mesec"])] = r

    def test_major_feasts_are_crveno_slovo(self):
        for dan, mesec in CRVENA_SLOVA:
            r = self.by_date.get((dan, mesec))
            self.assertIsNotNone(r, f"нема фиксног празника на {dan}.{mesec}")
            self.assertTrue(
                r["crveno_slovo"],
                f"{r['naziv']} ({dan}.{mesec}) мора бити црвено слово",
            )
