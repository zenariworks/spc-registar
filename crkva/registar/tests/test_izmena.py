"""Tests for the izmena_* edit views."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Domacinstvo, Osoba, Svestenik
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class IzmenaParohijanaTests(TestCase):
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
        cls.osoba = Osoba.objects.create(ime="Стари", prezime="Тест", pol="М")

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_parohijana", kwargs={"uid": self.osoba.uid})

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_clerk_can_open_and_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        r2 = self.client.post(
            self.url(),
            {"ime": "Нови", "prezime": "Тест", "pol": "М"},
        )
        self.assertEqual(r2.status_code, 302)
        self.osoba.refresh_from_db()
        self.assertEqual(self.osoba.ime, "Нови")

    def test_priest_cannot_open(self):
        self.client.force_login(self.priest)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 403)

    def test_unknown_uid_404(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("izmena_parohijana", kwargs={"uid": 999999}))
        self.assertEqual(r.status_code, 404)


class IzmenaSvestenikaTests(TestCase):
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
        cls.svestenik = Svestenik.objects.create(
            ime="Стари", prezime="Свештеник", zvanje="Јереј"
        )

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("izmena_svestenika", kwargs={"uid": self.svestenik.uid})

    def test_priest_can_edit(self):
        self.client.force_login(self.priest)
        r = self.client.post(
            self.url(),
            {"ime": "Стари", "prezime": "Свештеник", "zvanje": "Протојереј"},
        )
        self.assertEqual(r.status_code, 302)
        self.svestenik.refresh_from_db()
        self.assertEqual(self.svestenik.zvanje, "Протојереј")

    def test_clerk_cannot_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 403)


class IzmenaDomacinstvaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.domacin = Osoba.objects.create(ime="Стефан", prezime="Стефан", pol="М")
        cls.domacinstvo = Domacinstvo.objects.create(domacin=cls.domacin)

    def test_clerk_can_edit(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            reverse("izmena_domacinstva", kwargs={"uid": self.domacinstvo.uid}),
            {
                "domacin": str(self.domacin.uid),
                "napomena": "промењено",
                "slavska_vodica": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.domacinstvo.refresh_from_db()
        self.assertEqual(self.domacinstvo.napomena, "промењено")
        self.assertTrue(self.domacinstvo.slavska_vodica)
