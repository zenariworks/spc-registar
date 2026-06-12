"""Тестови за `crtica` филтер — празна вредност → „-" на штампи."""

# pylint: disable=missing-function-docstring

from django.test import SimpleTestCase
from registar.templatetags.print_filters import crtica


class CrticaFilterTests(SimpleTestCase):
    """`crtica`: None/празно/празнине → „-"; иначе непромењена вредност."""

    def test_none_daje_crticu(self):
        self.assertEqual(crtica(None), "-")

    def test_prazan_string_daje_crticu(self):
        self.assertEqual(crtica(""), "-")

    def test_samo_razmaci_daju_crticu(self):
        self.assertEqual(crtica("   "), "-")

    def test_vrednost_se_cuva(self):
        self.assertEqual(crtica("Београд"), "Београд")

    def test_nula_nije_prazna(self):
        self.assertEqual(crtica(0), "0")
