"""Тестови за брзе AJAX endpoint-е (особа/храм/адреса) из модала.

Покрива гране ван „срећног пута“: погрешан метод (405), валидација (400),
дедупликација (get_or_create / постојећи ред), и prefill GET за измену
адресе. Issue #222 — views/brzi_view.py био на 48%.
"""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Adresa, Hram
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class BrziViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        # Канцеларија има права за osoba/domacinstvo/krstenje/vencanje.
        cls.user = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.user, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    # --- особа ---
    def test_osoba_get_rejected_405(self):
        r = self.client.get(reverse("brzi_unos_osobe"))
        self.assertEqual(r.status_code, 405)

    def test_osoba_missing_name_400(self):
        r = self.client.post(reverse("brzi_unos_osobe"), {"ime": "", "prezime": "X"})
        self.assertEqual(r.status_code, 400)

    def test_osoba_invalid_pol_400(self):
        r = self.client.post(
            reverse("brzi_unos_osobe"),
            {"ime": "А", "prezime": "Б", "pol": "Q"},
        )
        self.assertEqual(r.status_code, 400)

    def test_osoba_valid_returns_id(self):
        r = self.client.post(
            reverse("brzi_unos_osobe"),
            {"ime": "Ново", "prezime": "Лице", "pol": "М"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("id", r.json())

    # --- храм ---
    def test_hram_get_rejected_405(self):
        r = self.client.get(reverse("brzi_unos_hrama"))
        self.assertEqual(r.status_code, 405)

    def test_hram_missing_naziv_400(self):
        r = self.client.post(reverse("brzi_unos_hrama"), {"naziv": ""})
        self.assertEqual(r.status_code, 400)

    def test_hram_create_and_dedup(self):
        r1 = self.client.post(
            reverse("brzi_unos_hrama"), {"naziv": "Свети Сава", "mesto": "Београд"}
        )
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(
            reverse("brzi_unos_hrama"), {"naziv": "Свети Сава", "mesto": "Београд"}
        )
        # Исти (naziv, mesto) → исти ред, без дупликата.
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        self.assertEqual(Hram.objects.filter(naziv="Свети Сава").count(), 1)

    # --- нова адреса ---
    def test_adresa_get_rejected_405(self):
        r = self.client.get(reverse("brzi_unos_adrese"))
        self.assertEqual(r.status_code, 405)

    def test_adresa_empty_400(self):
        r = self.client.post(reverse("brzi_unos_adrese"), {"ulica": "", "mesto": ""})
        self.assertEqual(r.status_code, 400)

    def test_adresa_create_and_dedup(self):
        payload = {"ulica": "Кнеза Милоша", "broj": "5", "mesto": "Београд"}
        r1 = self.client.post(reverse("brzi_unos_adrese"), payload)
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.post(reverse("brzi_unos_adrese"), payload)
        # Постојећа адреса се поново користи (case-insensitive).
        self.assertEqual(r1.json()["id"], r2.json()["id"])
        self.assertEqual(Adresa.objects.filter(ulica="Кнеза Милоша").count(), 1)

    # --- измена адресе ---
    def test_izmena_get_returns_prefill(self):
        a = Adresa.objects.create(ulica="Стара", broj="1", mesto="Ниш")
        r = self.client.get(reverse("brzi_izmena_adrese", kwargs={"uid": a.uid}))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["ulica"], "Стара")
        self.assertEqual(data["mesto"], "Ниш")

    def test_izmena_post_updates(self):
        a = Adresa.objects.create(ulica="Стара", broj="1", mesto="Ниш")
        r = self.client.post(
            reverse("brzi_izmena_adrese", kwargs={"uid": a.uid}),
            {"ulica": "Нова", "broj": "9", "broj_stana": "", "mesto": "Ниш"},
        )
        self.assertEqual(r.status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.ulica, "Нова")
        self.assertEqual(a.broj, "9")
