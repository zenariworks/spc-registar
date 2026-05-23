"""Verify the unified krstenje template renders full names + supports view/edit toggle.

Covers two regressions:
- Дете and Кум static rows used to render only `ime_*` (no `prezime_*`) on the
  detail page. Both must now include `prezime_deteta` / `prezime_kuma`.
- The unified template should respond on /krstenje/<uid>/ (view), /unos/krstenje/
  (create), and /izmena/krstenje/<uid>/ (edit) with the expected `data-mode`.
"""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Krstenje, Osoba
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class KrstenjeFullNameAndToggleTests(TestCase):
    """Asserts dete/kum surnames are rendered + toggle-mode HTML is present."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc-krst", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.dete = Osoba.objects.create(ime="Дете", prezime="Презименко", pol="М")
        cls.otac = Osoba.objects.create(ime="Отац", prezime="Презименко", pol="М")
        cls.majka = Osoba.objects.create(ime="Мајка", prezime="Презименко", pol="Ж")
        cls.kum = Osoba.objects.create(ime="Кум", prezime="Кумовић", pol="М")
        cls.krstenje = Krstenje.objects.create(
            dete=cls.dete,
            otac=cls.otac,
            majka=cls.majka,
            kum=cls.kum,
            datum=datetime.date(2020, 1, 1),
            knjiga="1",
            strana="2",
            broj="3",
            godina_registracije=2020,
            redni_broj=1,
            vanbracno=False,
            blizanac=False,
            telesna_mana=False,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    def test_detail_renders_full_name_for_dete(self):
        url = reverse("krstenje_detail", kwargs={"uid": self.krstenje.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        body = r.content.decode("utf-8")
        self.assertIn("Презименко", body)
        # Both ime and prezime of дете must appear (full name fix).
        self.assertIn("Дете Презименко", body)

    def test_detail_renders_full_name_for_kum(self):
        url = reverse("krstenje_detail", kwargs={"uid": self.krstenje.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        body = r.content.decode("utf-8")
        # ime + prezime kuma must appear together.
        self.assertIn("Кум Кумовић", body)

    def test_detail_uses_unified_template_and_view_mode(self):
        url = reverse("krstenje_detail", kwargs={"uid": self.krstenje.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/krstenje.html")
        body = r.content.decode("utf-8")
        self.assertIn("data-edit-toggle-root", body)
        self.assertIn('data-mode="view"', body)
        # The hidden form widgets must be present in the DOM for the toggle.
        self.assertIn("<input", body)

    def test_izmena_renders_unified_template_in_edit_mode(self):
        url = reverse("izmena_krstenja", kwargs={"uid": self.krstenje.uid})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/krstenje.html")
        body = r.content.decode("utf-8")
        self.assertIn('data-mode="edit"', body)

    def test_unos_renders_unified_template_in_edit_mode_no_instance(self):
        url = reverse("unos_krstenja")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/krstenje.html")
        body = r.content.decode("utf-8")
        self.assertIn('data-mode="edit"', body)
