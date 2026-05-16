"""Tests for the unos_domacinstva view + form."""

# pylint: disable=missing-function-docstring  # test names describe intent

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Osoba
from tenants.models import Role, Tenant, UserMembership


class UnosDomacinstvaViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.priest = User.objects.create_user(username="svest", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.admin = User.objects.create_superuser(
            username="root", password="x", email="r@x.test"
        )
        cls.domacin = Osoba.objects.create(ime="Стефан", prezime="Стефановић", pol="М")

    def setUp(self):
        self.client = Client()

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(reverse("unos_domacinstva"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_clerk_can_open_form(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("unos_domacinstva"))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/unos_domacinstva.html")

    def test_priest_cannot_open_form(self):
        self.client.force_login(self.priest)
        r = self.client.get(reverse("unos_domacinstva"))
        self.assertEqual(r.status_code, 403)

    def test_clerk_can_post_and_create_domacinstvo(self):
        self.client.force_login(self.clerk)
        before = Domacinstvo.objects.count()
        r = self.client.post(
            reverse("unos_domacinstva"),
            {
                "domacin": str(self.domacin.uid),
                "slavska_vodica": "on",
                "vaskrsnja_vodica": "",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Domacinstvo.objects.count(), before + 1)
        d = Domacinstvo.objects.get(domacin=self.domacin)
        self.assertTrue(d.slavska_vodica)
        self.assertFalse(d.vaskrsnja_vodica)

    def test_priest_cannot_post(self):
        self.client.force_login(self.priest)
        before = Domacinstvo.objects.count()
        r = self.client.post(
            reverse("unos_domacinstva"),
            {"domacin": str(self.domacin.uid)},
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Domacinstvo.objects.count(), before)

    def test_admin_can_post(self):
        self.client.force_login(self.admin)
        before = Domacinstvo.objects.count()
        r = self.client.post(
            reverse("unos_domacinstva"),
            {"domacin": str(self.domacin.uid)},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Domacinstvo.objects.count(), before + 1)

    def test_invalid_post_redisplays_form_with_errors(self):
        self.client.force_login(self.clerk)
        r = self.client.post(reverse("unos_domacinstva"), {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)
