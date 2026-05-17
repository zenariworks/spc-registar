"""Tests for the unos_svestenika view + form."""

# pylint: disable=missing-function-docstring  # test names describe intent

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Svestenik
from tenants.models import Role, Tenant, UserMembership


class UnosSvestenikaViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.priest = User.objects.create_user(username="svest", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.admin = User.objects.create_superuser(
            username="root", password="x", email="r@x.test"
        )

    def setUp(self):
        self.client = Client()

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(reverse("unos_svestenika"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_priest_can_open_form(self):
        self.client.force_login(self.priest)
        r = self.client.get(reverse("unos_svestenika"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/svestenik.html")
        self.assertIn("form", r.context)

    def test_clerk_cannot_open_form(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("unos_svestenika"))
        self.assertEqual(r.status_code, 403)

    def test_priest_can_post_and_create_svestenik(self):
        self.client.force_login(self.priest)
        before = Svestenik.objects.count()
        r = self.client.post(
            reverse("unos_svestenika"),
            {
                "ime": "Никола",
                "prezime": "Тестић",
                "zvanje": "Јереј",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Svestenik.objects.count(), before + 1)
        s = Svestenik.objects.get(ime="Никола", prezime="Тестић")
        self.assertEqual(s.zvanje, "Јереј")

    def test_clerk_cannot_post(self):
        self.client.force_login(self.clerk)
        before = Svestenik.objects.count()
        r = self.client.post(
            reverse("unos_svestenika"),
            {"ime": "Не", "prezime": "Може", "zvanje": "Јереј"},
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Svestenik.objects.count(), before)

    def test_admin_can_post(self):
        self.client.force_login(self.admin)
        before = Svestenik.objects.count()
        r = self.client.post(
            reverse("unos_svestenika"),
            {"ime": "Админ", "prezime": "Свештеник", "zvanje": "Протојереј"},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Svestenik.objects.count(), before + 1)

    def test_invalid_post_redisplays_form_with_errors(self):
        self.client.force_login(self.priest)
        r = self.client.post(reverse("unos_svestenika"), {"ime": "Само име"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)
