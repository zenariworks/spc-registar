from django.test import TestCase

import uuid

from .models import Parohijan


class UnitTestCase(TestCase):
    def setUp(self):
        Parohijan.objects.create(uid=2023)

    def test_animals_can_speak(self):
        """Animals that can speak are correctly identified"""
        godina = Parohijan.objects.get(uid=2023)
        self.assertEqual(str(godina), 2023)
