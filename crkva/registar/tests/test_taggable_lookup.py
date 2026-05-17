"""Tests for the taggable lookup pattern."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Parohijan, Zanimanje
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class TaggableLookupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.user = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.user, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.existing_zanimanje = Zanimanje.objects.create(naziv="Учитељ")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_select_existing_lookup_by_pk(self):
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Тест",
                "prezime": "Иван",
                "pol": "М",
                "zanimanje": str(self.existing_zanimanje.pk),
            },
        )
        self.assertEqual(r.status_code, 302)
        p = Parohijan.objects.get(ime="Тест", prezime="Иван")
        self.assertEqual(p.zanimanje, self.existing_zanimanje)

    def test_create_new_lookup_from_typed_string(self):
        before = Zanimanje.objects.count()
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Нови",
                "prezime": "Иван",
                "pol": "М",
                "zanimanje": "Програмер",
                "veroispovest": "Православна",
                "narodnost": "Српска",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Zanimanje.objects.count(), before + 1)
        new = Zanimanje.objects.get(naziv="Програмер")
        p = Parohijan.objects.get(ime="Нови", prezime="Иван")
        self.assertEqual(p.zanimanje, new)
        self.assertEqual(p.veroispovest.naziv, "Православна")
        self.assertEqual(p.narodnost.naziv, "Српска")

    def test_typed_string_matches_existing_creates_no_duplicate(self):
        before = Zanimanje.objects.count()
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Дупликат",
                "prezime": "Тест",
                "pol": "М",
                "zanimanje": "Учитељ",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Zanimanje.objects.count(), before)
        p = Parohijan.objects.get(ime="Дупликат")
        self.assertEqual(p.zanimanje, self.existing_zanimanje)
