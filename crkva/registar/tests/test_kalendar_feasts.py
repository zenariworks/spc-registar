"""Регресија за #335: фиксни велики празници на грађанском (грегоријанском)
календару.

Раније су две ставке `MAJOR_FEASTS` држале јулијанске датуме
(Ваведење 21.11, Ђурђевдан 19.5), па се празник болдирао на погрешан дан
сваке године. Фикстура `slave.jsonl` већ носи грађанске датуме
(Ваведење 4.12, Ђурђевдан 6.5).
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

import datetime as dt

from django.test import SimpleTestCase
from registar.kalendar import MAJOR_FEASTS, is_major_feast


class MajorFeastsGregorianTests(SimpleTestCase):
    def test_vavedenje_on_civil_date(self):
        """Ваведење је 4.12 (грегоријански), не 21.11 (јулијански)."""
        self.assertEqual(MAJOR_FEASTS.get((12, 4)), "Ваведење")
        self.assertNotIn((11, 21), MAJOR_FEASTS)

    def test_djurdjevdan_on_civil_date(self):
        """Ђурђевдан је 6.5 (грегоријански), не 19.5."""
        self.assertEqual(MAJOR_FEASTS.get((5, 6)), "Ђурђевдан")
        self.assertNotIn((5, 19), MAJOR_FEASTS)

    def test_is_major_feast_fixed_gregorian(self):
        """`is_major_feast` препознаје фиксне празнике по грађанском датуму."""
        self.assertTrue(is_major_feast(dt.date(2026, 12, 4), []))
        self.assertTrue(is_major_feast(dt.date(2026, 5, 6), []))
        self.assertFalse(is_major_feast(dt.date(2026, 11, 21), []))
        self.assertFalse(is_major_feast(dt.date(2026, 5, 19), []))
