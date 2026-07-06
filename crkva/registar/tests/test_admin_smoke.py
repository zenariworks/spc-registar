"""Smoke тестови за Django админ регистар модела (#334).

Пре исправке су Osoba add/change и претрага пуцали (FieldError због
`zanimanje__naziv` у fieldsets и `adresa__naziv` у search_fields), а Krstenje
add је пуцао на чувању (NOT NULL — обавезна поља изостављена из forme). Ови
тестови учитавају changelist/add сваке регистроване регистарске класе и
проверавају да ниједна не враћа 500.
"""

from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class AdminSmokeTest(TestCase):
    """Свака регистарска админ страница се учита без 500."""

    @classmethod
    def setUpTestData(cls):
        cls.models = [
            m
            for m in admin.site._registry
            if m._meta.app_label == "registar" and not m._meta.proxy
        ]

    def setUp(self):
        self.client = Client()
        user = get_user_model().objects.create_superuser(
            username="admin-smoke", email="admin@smoke.test", password="x"
        )
        self.client.force_login(user)

    def _url(self, model, kind):
        meta = model._meta
        return reverse(f"admin:{meta.app_label}_{meta.model_name}_{kind}")

    def test_registar_models_registered(self):
        """Барем кључни регистарски модели су у админу."""
        names = {m._meta.model_name for m in self.models}
        for expected in ("osoba", "krstenje", "vencanje", "domacinstvo", "svestenik"):
            self.assertIn(expected, names)

    def test_changelist_loads(self):
        """Changelist сваке класе враћа 200 (не 500)."""
        for model in self.models:
            with self.subTest(model=model._meta.model_name):
                resp = self.client.get(self._url(model, "changelist"))
                self.assertEqual(resp.status_code, 200)

    def test_changelist_search_loads(self):
        """Претрага (?q=) не пуца на неисправном search_fields (нпр. adresa__naziv)."""
        for model in self.models:
            with self.subTest(model=model._meta.model_name):
                resp = self.client.get(self._url(model, "changelist"), {"q": "тест"})
                self.assertEqual(resp.status_code, 200)

    def test_add_form_loads(self):
        """Add страница сваке класе се рендерује (не 500 на FieldError у fieldsets)."""
        for model in self.models:
            with self.subTest(model=model._meta.model_name):
                resp = self.client.get(self._url(model, "add"))
                self.assertEqual(resp.status_code, 200)

    def test_krstenje_add_post_does_not_500(self):
        """Празан POST на Krstenje add враћа валидациону грешку (200), не NOT NULL 500."""
        Krstenje = apps.get_model("registar", "Krstenje")
        url = self._url(Krstenje, "add")
        resp = self.client.post(url, data={})
        # Пре исправке: fieldsets је изостављао обавезна поља → IntegrityError 500.
        # После: подразумевана форма враћа 200 са грешкама валидације.
        self.assertNotEqual(resp.status_code, 500)
        self.assertEqual(resp.status_code, 200)
