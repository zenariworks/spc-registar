"""
Тестови за template тагове и филтере.
"""

import datetime

from django.test import TestCase
from registar.templatetags.julian_dates import (
    gregorian_to_julian,
    to_julian_date,
    to_julian_date_numeric,
)


class GregorianToJulianTestCase(TestCase):
    """Тестови за конверзију грегоријанског у јулијански датум."""

    def test_standard_date(self):
        """Стандардна конверзија датума (13 дана разлике)."""
        gregorian = datetime.date(2024, 1, 20)
        julian = gregorian_to_julian(gregorian)
        expected = datetime.date(2024, 1, 7)
        self.assertEqual(julian, expected)

    def test_month_boundary(self):
        """Конверзија преко границе месеца."""
        gregorian = datetime.date(2024, 2, 10)
        julian = gregorian_to_julian(gregorian)
        expected = datetime.date(2024, 1, 28)
        self.assertEqual(julian, expected)

    def test_year_boundary(self):
        """Конверзија преко границе године."""
        gregorian = datetime.date(2024, 1, 10)
        julian = gregorian_to_julian(gregorian)
        expected = datetime.date(2023, 12, 28)
        self.assertEqual(julian, expected)

    def test_christmas(self):
        """Православни Божић (7. јануар грегоријански = 25. децембар јулијански)."""
        gregorian = datetime.date(2024, 1, 7)
        julian = gregorian_to_julian(gregorian)
        expected = datetime.date(2023, 12, 25)
        self.assertEqual(julian, expected)


class ToJulianDateFilterTestCase(TestCase):
    """Тестови за to_julian_date template филтер."""

    def test_same_month_format(self):
        """Формат када су оба датума у истом месецу."""
        date = datetime.date(2024, 3, 20)
        result = to_julian_date(date)
        self.assertIn("март", result)
        self.assertIn("20", result)
        self.assertIn("7", result)

    def test_different_month_format(self):
        """Формат када су датуми у различитим месецима."""
        date = datetime.date(2024, 2, 10)
        result = to_julian_date(date)
        self.assertIn("фебруар", result)
        self.assertIn("јануар", result)

    def test_none_input(self):
        """None вредност враћа празан стринг."""
        result = to_julian_date(None)
        self.assertEqual(result, "")

    def test_string_input(self):
        """Стринг улаз враћа празан стринг."""
        result = to_julian_date("2024-01-20")
        self.assertEqual(result, "")

    def test_year_included(self):
        """Година је укључена у резултат."""
        date = datetime.date(2024, 5, 15)
        result = to_julian_date(date)
        self.assertIn("2024", result)

    def test_orthodox_christmas(self):
        """Православни Божић приказује децембар у јулијанском делу."""
        date = datetime.date(2024, 1, 7)
        result = to_julian_date(date)
        self.assertIn("јануар", result)
        self.assertIn("децембар", result)
        self.assertIn("25", result)


class ToJulianDateNumericFilterTestCase(TestCase):
    """Тестови за нумерички julian_date_numeric филтер (штампа крштенице)."""

    def test_same_month_shows_julian_day(self):
        result = to_julian_date_numeric(datetime.date(2017, 3, 22))
        self.assertEqual(result, "2017.03.22 / 09")

    def test_year_rollover_shows_full_julian_date(self):
        result = to_julian_date_numeric(datetime.date(2024, 1, 5))
        self.assertEqual(result, "2024.01.05 / 2023.12.23")

    def test_month_rollover_shows_full_julian_date(self):
        result = to_julian_date_numeric(datetime.date(2020, 2, 1))
        self.assertEqual(result, "2020.02.01 / 2020.01.19")

    def test_none_input(self):
        self.assertEqual(to_julian_date_numeric(None), "")

    def test_string_input(self):
        self.assertEqual(to_julian_date_numeric("2024-01-20"), "")
