"""Regression: списак домаћинстава мора имати empty state и next-page-marker."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Osoba

User = get_user_model()


class DomacinstvoListEmptyStateTests(TestCase):
    """Bug 2: списак домаћинстава мора имати empty state и next-page-marker."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)

    def test_empty_list_renders_empty_state(self):
        Domacinstvo.objects.all().delete()
        r = self.client.get(reverse("domacinstva"))
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn("Нема домаћинстава", body)
        self.assertIn("spisak__empty", body)

    def test_next_page_marker_present_when_pagination_overflows(self):
        # paginate_by=20 → create 25 households to force a second page
        for i in range(25):
            o = Osoba.objects.create(ime=f"Дом{i}", prezime="Тест", parohijan=True)
            Domacinstvo.objects.create(domacin=o)
        r = self.client.get(reverse("domacinstva"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "next-page-marker")
        self.assertContains(r, 'data-next-page="2"')
