from django.test import TestCase
from .models import Set


class UnitTestCase(TestCase):
    def setUp(self):
        Set.objects.create(hsp_godina=2023)

    def test_animals_can_speak(self):
        """Animals that can speak are correctly identified"""
        godina = Set.objects.get(hsp_godina=2023)
        self.assertEqual(str(godina), 2023)
