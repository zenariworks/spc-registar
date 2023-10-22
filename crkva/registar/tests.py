from django.test import TestCase

import uuid

from .models import Osoba


class UnitTestCase(TestCase):
    def setUp(self):
        Osoba.objects.create(uid=2023)

    def test_animals_can_speak(self):
        """Animals that can speak are correctly identified"""
        godina = Osoba.objects.get(uid=2023)
        self.assertEqual(str(godina), 2023)
