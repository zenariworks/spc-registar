"""Тестови за redni_rec филтер (број → редни број речима).

Покрива све гране: празно/None → „није уписано“, вредност < 1 → „није
уписано“, опсег 1–20 (реч), > 20 („N.“), и не-број (непромењено).
Issue #222 — филтер уведен у #243 имао је само 53% покривености.
"""

# pylint: disable=missing-function-docstring

from django.test import SimpleTestCase
from registar.templatetags.ordinal_filters import (
    NIJE_UPISANO,
    redni_rec,
    redni_rec_m,
)


class RedniRecTests(SimpleTestCase):
    """Тестови за redni_rec (средњи род, „дете по реду")."""

    def test_none_is_nije_upisano(self):
        self.assertEqual(redni_rec(None), NIJE_UPISANO)

    def test_empty_string_is_nije_upisano(self):
        self.assertEqual(redni_rec(""), NIJE_UPISANO)

    def test_zero_is_nije_upisano(self):
        self.assertEqual(redni_rec(0), NIJE_UPISANO)

    def test_negative_is_nije_upisano(self):
        self.assertEqual(redni_rec(-3), NIJE_UPISANO)

    def test_first(self):
        self.assertEqual(redni_rec(1), "прво")

    def test_seventh(self):
        self.assertEqual(redni_rec(7), "седмо")

    def test_twentieth_upper_bound(self):
        self.assertEqual(redni_rec(20), "двадесето")

    def test_above_twenty_numeric_form(self):
        self.assertEqual(redni_rec(21), "21.")

    def test_numeric_string_coerced(self):
        self.assertEqual(redni_rec("5"), "пето")

    def test_non_numeric_returned_unchanged(self):
        self.assertEqual(redni_rec("abc"), "abc")


class RedniRecMTests(SimpleTestCase):
    """Тестови за redni_rec_m (мушки род, „који брак")."""

    def test_none_is_nije_upisano(self):
        self.assertEqual(redni_rec_m(None), NIJE_UPISANO)

    def test_first_masculine(self):
        self.assertEqual(redni_rec_m(1), "први")

    def test_second_masculine(self):
        self.assertEqual(redni_rec_m(2), "други")

    def test_twentieth(self):
        self.assertEqual(redni_rec_m(20), "двадесети")

    def test_above_twenty_numeric_form(self):
        self.assertEqual(redni_rec_m(21), "21.")
