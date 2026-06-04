"""
Тестови за template тагове и филтере.
"""

import datetime

from django.test import TestCase
from registar.templatetags.julian_dates import gregorian_to_julian, to_julian_date


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

    def test_same_year_no_duplicate_year(self):
        """Иста година: година се не понавља."""
        result = to_julian_date(datetime.date(2022, 10, 10))
        self.assertEqual(result, "2022, октобар 10 / септембар 27")

    def test_year_rollover_shows_julian_year(self):
        """Прелаз у претходну годину приказује јулијанску годину."""
        result = to_julian_date(datetime.date(2024, 1, 5))
        self.assertEqual(result, "2024, јануар 5 / 2023, децембар 23")
