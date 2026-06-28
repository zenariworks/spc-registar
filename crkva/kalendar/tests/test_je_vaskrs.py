"""Tests for Slava.je_vaskrs / get_vaskrs — robust Vaskrs detection (#325)."""

# pylint: disable=missing-function-docstring

from django.test import TestCase
from kalendar.models import Slava


class JeVaskrsTests(TestCase):
    def test_zero_offset_movable_is_vaskrs(self):
        s = Slava.objects.create(
            naziv="Васкрс", pokretni=True, offset_dani=0, offset_nedelje=0
        )
        self.assertTrue(s.je_vaskrs)

    def test_null_offset_movable_is_vaskrs(self):
        # Offsets may be NULL rather than 0 for the anchor feast.
        s = Slava.objects.create(naziv="Васкрс", pokretni=True)
        self.assertTrue(s.je_vaskrs)

    def test_offset_movable_is_not_vaskrs(self):
        s = Slava.objects.create(
            naziv="Васкрсни понедељак", pokretni=True, offset_dani=1
        )
        self.assertFalse(s.je_vaskrs)

    def test_fixed_feast_is_not_vaskrs(self):
        s = Slava.objects.create(naziv="Никољдан", pokretni=False, mesec=12, dan=19)
        self.assertFalse(s.je_vaskrs)

    def test_get_vaskrs_returns_the_anchor(self):
        Slava.objects.create(naziv="Духови", pokretni=True, offset_dani=49)
        vaskrs = Slava.objects.create(
            naziv="Васкрс", pokretni=True, offset_dani=0, offset_nedelje=0
        )
        self.assertEqual(Slava.get_vaskrs(), vaskrs)

    def test_get_vaskrs_none_when_absent(self):
        Slava.objects.create(naziv="Никољдан", pokretni=False, mesec=12, dan=19)
        self.assertIsNone(Slava.get_vaskrs())
