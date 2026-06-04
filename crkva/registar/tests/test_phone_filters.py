"""Тестови за phone_filters template филтере (format_phone, tel_link, phone_icon).

Покрива и објекте PhoneNumber и сирове стрингове, укључујући fallback гране
за неважеће улазе које phonenumbers.parse одбија (issue #222 — подизање
покривености templatetags/, која је била најнижа у апликацији: 20%).
"""

# pylint: disable=missing-function-docstring

from django.test import SimpleTestCase
from phonenumber_field.phonenumber import PhoneNumber
from registar.templatetags.phone_filters import (
    format_phone,
    phone_icon,
    tel_link,
)


class FormatPhoneTests(SimpleTestCase):
    def test_empty_returns_empty(self):
        self.assertEqual(format_phone(""), "")
        self.assertEqual(format_phone(None), "")

    def test_phonenumber_object_uses_as_national(self):
        pn = PhoneNumber.from_string("+381641234567")
        self.assertEqual(format_phone(pn), pn.as_national)

    def test_valid_rs_string_formats_national(self):
        # Рашчлањиво → национални формат са груписаним цифрама.
        self.assertEqual(format_phone("0641234567"), "064 1234567")

    def test_unparseable_string_returned_unchanged(self):
        self.assertEqual(format_phone("није-број"), "није-број")


class TelLinkTests(SimpleTestCase):
    def test_empty_returns_empty(self):
        self.assertEqual(tel_link(""), "")
        self.assertEqual(tel_link(None), "")

    def test_phonenumber_object_uses_e164(self):
        pn = PhoneNumber.from_string("+381641234567")
        self.assertEqual(tel_link(pn), "+381641234567")

    def test_valid_string_to_e164(self):
        self.assertEqual(tel_link("0641234567"), "+381641234567")

    def test_unparseable_no_digits_returns_empty(self):
        # phonenumbers одбија → fallback; нема цифара → празно.
        self.assertEqual(tel_link("abc"), "")

    def test_unparseable_leading_zero_branch(self):
        # Одбијено рашчлањивање, цифре „0“ → +381 без водеће нуле.
        self.assertEqual(tel_link("0abc"), "+381")

    def test_unparseable_other_digits_branch(self):
        # Одбијено рашчлањивање, цифре не почињу 0/381 → +381 + цифре.
        self.assertEqual(tel_link("abc1"), "+3811")


class PhoneIconTests(SimpleTestCase):
    def test_empty_default_icon(self):
        self.assertEqual(phone_icon(""), "fa-phone")
        self.assertEqual(phone_icon(None), "fa-phone")

    def test_mobile_number_icon(self):
        self.assertEqual(phone_icon("0641234567"), "fa-mobile-screen")

    def test_fixed_line_icon(self):
        # Београдски фиксни (011) → икона телефона.
        self.assertEqual(phone_icon("0112345678"), "fa-phone")

    def test_unparseable_mobile_heuristic(self):
        # Нерашчлањив, али почиње са 06 → хеуристика каже мобилни.
        self.assertEqual(phone_icon("06/нешто"), "fa-mobile-screen")

    def test_unparseable_default(self):
        self.assertEqual(phone_icon("xyz"), "fa-phone")
