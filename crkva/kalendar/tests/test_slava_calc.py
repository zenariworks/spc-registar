"""Тестови за прорачуне у моделу Slava (Васкрс, датум, пост, назив месеца).

Покрива calc_vaskrs (Гаусов алгоритам), get_datum (фиксни/покретни/празан),
get_post (без поста и са границама) и get_mesec_naziv. Чисти прорачуни
без базе. Issue #222 — kalendar/models/slava.py био на 64%.
"""

# pylint: disable=missing-function-docstring

import datetime

from django.test import SimpleTestCase
from kalendar.models.slava import Slava


class CalcVaskrsTests(SimpleTestCase):
    def test_known_year_2024(self):
        # Православни Васкрс 2024 (грегоријански) = 5. мај.
        self.assertEqual(Slava.sracunaj_vaskrs(2024), datetime.date(2024, 5, 5))

    def test_known_year_2023(self):
        self.assertEqual(Slava.sracunaj_vaskrs(2023), datetime.date(2023, 4, 16))


class GetDatumTests(SimpleTestCase):
    def test_fixed_feast(self):
        s = Slava(naziv="Усековање", opsti_naziv="Усековање", dan=28, mesec=8)
        self.assertEqual(s.get_datum(2024), datetime.date(2024, 8, 28))

    def test_movable_feast_uses_offset(self):
        # Покретни празник 49 дана после Васкрса 2024 (5. мај).
        s = Slava(naziv="X", opsti_naziv="X", pokretni=True, pomak_dani=49)
        self.assertEqual(s.get_datum(2024), datetime.date(2024, 6, 23))

    def test_movable_feast_weeks_offset(self):
        s = Slava(naziv="X", opsti_naziv="X", pokretni=True, pomak_nedelje=1)
        self.assertEqual(s.get_datum(2024), datetime.date(2024, 5, 12))

    def test_no_date_returns_none(self):
        s = Slava(naziv="X", opsti_naziv="X")
        self.assertIsNone(s.get_datum(2024))


class GetPostTests(SimpleTestCase):
    def test_no_fast_returns_none(self):
        s = Slava(naziv="X", opsti_naziv="X", post=False)
        self.assertIsNone(s.get_post(2024))

    def test_fast_returns_start_end_tuple(self):
        s = Slava(naziv="X", opsti_naziv="X", post=True, post_od=-48, post_do=0)
        start, end = s.get_post(2024)
        self.assertEqual(start, datetime.date(2024, 3, 18))
        self.assertEqual(end, datetime.date(2024, 5, 5))


class GetMesecNazivTests(SimpleTestCase):
    def test_known_month(self):
        s = Slava(naziv="X", opsti_naziv="X", dan=28, mesec=8)
        self.assertEqual(s.get_mesec_naziv(), "август")

    def test_no_month_empty(self):
        s = Slava(naziv="X", opsti_naziv="X")
        self.assertEqual(s.get_mesec_naziv(), "")
