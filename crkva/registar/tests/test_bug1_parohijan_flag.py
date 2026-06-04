"""Regression: quick-add parohijan flag.

A bare quick-add (no toggle value) defaults to parohijan=True so the
person appears in /parohijani/. The modal's “парохијан” toggle can send
parohijan=0 for roles like a kum from another parish, who must NOT be
added to this parish roster (issue #22).
"""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Osoba
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class ParohijanFlagOnCreateTests(TestCase):
    """Bug 1: новокреирани парохијанин мора имати parohijan=True."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    def test_unos_parohijana_sets_parohijan_true(self):
        r = self.client.post(
            reverse("unos_parohijana"),
            {"ime": "Тест", "prezime": "Парохијан", "pol": "М"},
        )
        self.assertEqual(r.status_code, 302)
        osoba = Osoba.objects.get(ime="Тест", prezime="Парохијан")
        self.assertTrue(osoba.parohijan)

    def test_brzi_unos_osobe_sets_parohijan_true(self):
        r = self.client.post(
            reverse("brzi_unos_osobe"),
            {"ime": "Брзи", "prezime": "Унос", "pol": "Ж"},
        )
        self.assertEqual(r.status_code, 200)
        osoba = Osoba.objects.get(ime="Брзи", prezime="Унос")
        self.assertTrue(osoba.parohijan)

    def test_brzi_unos_osobe_parohijan_false_excluded_from_spisak(self):
        # Kum from another parish: toggle off → not a parishioner, not in list.
        r = self.client.post(
            reverse("brzi_unos_osobe"),
            {"ime": "Кум", "prezime": "Изван", "pol": "М", "parohijan": "0"},
        )
        self.assertEqual(r.status_code, 200)
        osoba = Osoba.objects.get(ime="Кум", prezime="Изван")
        self.assertFalse(osoba.parohijan)
        spisak = self.client.get(reverse("parohijani"))
        self.assertNotContains(spisak, "Кум Изван")

    def test_new_parohijan_appears_in_spisak(self):
        self.client.post(
            reverse("unos_parohijana"),
            {"ime": "Видљив", "prezime": "Тест", "pol": "М"},
        )
        r = self.client.get(reverse("parohijani"))
        self.assertContains(r, "Видљив Тест")
