"""Брзи AJAX unos за Свештеник и Парохија из dropdown модала (#233).

Покрива: метод (405), валидација (400), креирање (200), дедупликација
(filter-first), валидација звања, дозвола (свештенички ресурс), и
data-create-modal атрибуте на виџетима.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.forms.select2 import ParohijaSelect2Widget, SvestenikSelect2Widget
from registar.models import Parohija, Svestenik
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class BrziSvestenikParohijaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        # Свештенички ресурс има ADMIN (и SVESTENSTVO); KANCELARIJA нема.
        cls.admin = User.objects.create_user(username="adm", password="x")
        UserMembership.objects.create(
            user=cls.admin, tenant=cls.tenant, role=Role.ADMIN
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    # ------------------------------------------------------------- свештеник
    def test_svestenik_get_rejected_405(self):
        r = self.client.get(reverse("brzi_unos_svestenika"))
        self.assertEqual(r.status_code, 405)

    def test_svestenik_missing_name_400(self):
        r = self.client.post(
            reverse("brzi_unos_svestenika"),
            {"ime": "", "prezime": "", "zvanje": "јереј"},
        )
        self.assertEqual(r.status_code, 400)

    def test_svestenik_invalid_zvanje_400(self):
        r = self.client.post(
            reverse("brzi_unos_svestenika"),
            {"ime": "Петар", "prezime": "Петровић", "zvanje": "измишљено"},
        )
        self.assertEqual(r.status_code, 400)

    def test_svestenik_missing_zvanje_400(self):
        r = self.client.post(
            reverse("brzi_unos_svestenika"),
            {"ime": "Петар", "prezime": "Петровић", "zvanje": ""},
        )
        self.assertEqual(r.status_code, 400)

    def test_svestenik_create_and_dedup(self):
        payload = {"ime": "Петар", "prezime": "Петровић", "zvanje": "јереј"}
        r1 = self.client.post(reverse("brzi_unos_svestenika"), payload)
        self.assertEqual(r1.status_code, 200)
        self.assertIn("id", r1.json())
        r2 = self.client.post(reverse("brzi_unos_svestenika"), payload)
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        self.assertEqual(
            Svestenik.objects.filter(ime="Петар", prezime="Петровић").count(), 1
        )

    def test_svestenik_text_includes_zvanje(self):
        r = self.client.post(
            reverse("brzi_unos_svestenika"),
            {"ime": "Лазар", "prezime": "Лазић", "zvanje": "протојереј"},
        )
        self.assertIn("протојереј", r.json()["text"])

    def test_svestenik_forbidden_for_kancelarija(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            reverse("brzi_unos_svestenika"),
            {"ime": "Нико", "prezime": "Никић", "zvanje": "јереј"},
        )
        self.assertIn(r.status_code, (302, 403))
        self.assertFalse(Svestenik.objects.filter(prezime="Никић").exists())

    # -------------------------------------------------------------- парохија
    def test_parohija_get_rejected_405(self):
        r = self.client.get(reverse("brzi_unos_parohije"))
        self.assertEqual(r.status_code, 405)

    def test_parohija_missing_naziv_400(self):
        r = self.client.post(reverse("brzi_unos_parohije"), {"naziv": ""})
        self.assertEqual(r.status_code, 400)

    def test_parohija_create_and_dedup(self):
        r1 = self.client.post(reverse("brzi_unos_parohije"), {"naziv": "Прва парохија"})
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(reverse("brzi_unos_parohije"), {"naziv": "прва парохија"})
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        self.assertEqual(Parohija.objects.filter(naziv="Прва парохија").count(), 1)

    def test_parohija_forbidden_for_kancelarija(self):
        self.client.force_login(self.clerk)
        r = self.client.post(reverse("brzi_unos_parohije"), {"naziv": "Забрањена"})
        self.assertIn(r.status_code, (302, 403))
        self.assertFalse(Parohija.objects.filter(naziv="Забрањена").exists())

    # --------------------------------------------------------------- виџети
    def test_svestenik_widget_carries_create_attr(self):
        attrs = SvestenikSelect2Widget().build_attrs({})
        self.assertEqual(attrs.get("data-create-modal"), "svestenik-create-modal")

    def test_parohija_widget_carries_create_attr(self):
        attrs = ParohijaSelect2Widget().build_attrs({})
        self.assertEqual(attrs.get("data-create-modal"), "parohija-create-modal")
