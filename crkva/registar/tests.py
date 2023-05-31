from django.test import TestCase
from .models import Unit


class UnitTestCase(TestCase):
    def setUp(self):
        Unit.objects.create(name="aantal", code=None, symbol=None)
        Unit.objects.create(name="percentage", code="_P", symbol="%")

    def test_animals_can_speak(self):
        """Animals that can speak are correctly identified"""
        aantal = Unit.objects.get(name="aantal")
        percentage = Unit.objects.get(name="percentage")
        self.assertEqual(str(aantal), "aantal")
        self.assertEqual(str(percentage), "percentage")
