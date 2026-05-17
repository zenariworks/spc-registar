"""Tests confirming Slava is a shared model living in the public schema."""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django_tenants.utils import schema_context
from kalendar.models import Slava
from registar.models import Domacinstvo, Osoba
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class SlavaIsSharedTests(TestCase):
    """Slava lives in kalendar app and the public schema, not in registar."""

    def test_slava_app_label_is_kalendar(self):
        self.assertEqual(Slava._meta.app_label, "kalendar")

    def test_slava_db_table_is_slave(self):
        self.assertEqual(Slava._meta.db_table, "slave")

    def test_kalendar_is_in_shared_apps(self):
        from django.conf import settings

        self.assertIn("kalendar", settings.SHARED_APPS)
        self.assertNotIn("kalendar", settings.TENANT_APPS)

    def test_registar_no_longer_owns_slava(self):
        registar_models = {
            m.__name__ for m in apps.get_app_config("registar").get_models()
        }
        self.assertNotIn("Slava", registar_models)

    def test_slava_table_exists_in_public_schema(self):
        with schema_context("public"):
            with connection.cursor() as cursor:
                cursor.execute("SELECT to_regclass('public.slave')")
                row = cursor.fetchone()
                self.assertIsNotNone(row[0], "slave table missing from public schema")


class SlavaCrossSchemaFKTests(TestCase):
    """Domacinstvo.slava (tenant) references kalendar.Slava (public)."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.user = User.objects.create_user(username="cross", password="x")
        UserMembership.objects.create(
            user=cls.user, tenant=cls.tenant, role=Role.PREGLED
        )

    def test_fk_field_has_db_constraint_disabled(self):
        field = Domacinstvo._meta.get_field("slava")
        self.assertFalse(field.db_constraint)
        self.assertEqual(field.related_model, Slava)

    def test_create_domacinstvo_with_shared_slava(self):
        # Slava is created (and lives) in public schema.
        with schema_context("public"):
            slava = Slava.objects.create(naziv="Тест Слава", dan=15, mesec=8)

        # Domacinstvo (tenant table) references the public slava.
        osoba = Osoba.objects.create(ime="Крст", prezime="Тестић", pol="М")
        d = Domacinstvo.objects.create(domacin=osoba, slava=slava)

        # Re-fetch from tenant schema; the FK still resolves.
        fetched = Domacinstvo.objects.select_related("slava").get(pk=d.pk)
        self.assertEqual(fetched.slava.naziv, "Тест Слава")
        self.assertEqual(fetched.slava_id, slava.uid)

    def test_logged_in_tenant_user_lists_shared_slava(self):
        with schema_context("public"):
            slava = Slava.objects.create(naziv="Никољдан", dan=19, mesec=12)
        osoba = Osoba.objects.create(ime="Никола", prezime="Николић", pol="М")
        Domacinstvo.objects.create(domacin=osoba, slava=slava)

        self.client.force_login(self.user)
        response = self.client.get("/parohijani/")
        self.assertEqual(response.status_code, 200)
