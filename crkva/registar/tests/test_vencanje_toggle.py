"""Verify the unified vencanje template handles view, edit, and create paths."""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Osoba, Vencanje
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class VencanjeUnifiedTemplateTests(TestCase):
    """Asserts /vencanje/, /unos/vencanje/, /izmena/vencanje/ all use vencanje.html."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc-venc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.zenik = Osoba.objects.create(ime="Жеља", prezime="Жељовић", pol="М")
        cls.nevesta = Osoba.objects.create(ime="Нада", prezime="Надовић", pol="Ж")
        cls.vencanje = Vencanje.objects.create(
            zenik=cls.zenik,
            nevesta=cls.nevesta,
            datum=datetime.date(2020, 6, 6),
            knjiga="1",
            strana="1",
            broj="1",
            redni_broj=1,
            godina_registracije=2020,
            razresenje=False,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    def test_detail_uses_unified_template_and_view_mode(self):
        url = reverse("vencanje_detail", kwargs={"uid": self.vencanje.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/vencanje.html")
        body = r.content.decode("utf-8")
        self.assertIn("data-edit-toggle-root", body)
        self.assertIn('data-mode="view"', body)
        # The hidden form widgets must be present for the in-place toggle.
        self.assertIn("<input", body)

    def test_izmena_renders_in_edit_mode(self):
        url = reverse("izmena_vencanja", kwargs={"uid": self.vencanje.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/vencanje.html")
        body = r.content.decode("utf-8")
        self.assertIn('data-mode="edit"', body)

    def test_unos_renders_in_edit_mode_no_instance(self):
        url = reverse("unos_vencanja")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/vencanje.html")
        body = r.content.decode("utf-8")
        self.assertIn('data-mode="edit"', body)
