"""Tests for the tenant-switch endpoint."""

# pylint: disable=missing-function-docstring  # test names already describe intent

from django.contrib.auth.models import User
from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse
from tenants.middleware import SESSION_TENANT_KEY
from tenants.models import Tenant, UserMembership


class SwitchTenantViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant_a = Tenant.objects.get(schema_name="test_tenant")
        # bulk_create bypasses TenantMixin.save() so we don't try to provision
        # new Postgres schemas from inside the active tenant schema.
        Tenant.objects.bulk_create(
            [
                Tenant(
                    schema_name="test_tenant_b",
                    naziv="Test B",
                    is_active=True,
                ),
                Tenant(
                    schema_name="test_tenant_off",
                    naziv="Test Off",
                    is_active=False,
                ),
            ]
        )
        cls.tenant_b = Tenant.objects.get(schema_name="test_tenant_b")
        cls.tenant_inactive = Tenant.objects.get(schema_name="test_tenant_off")

        cls.superuser = User.objects.create_superuser(
            username="root", password="x", email="root@test"
        )
        cls.user = User.objects.create_user(username="alice", password="x")
        UserMembership.objects.create(user=cls.user, tenant=cls.tenant_a)

    def setUp(self):
        # Each test starts on the default test_tenant schema; ensure that
        # the User/session/Tenant lookups in middleware see consistent state.
        connection.set_tenant(self.tenant_a)
        self.client = Client()

    def url(self, tenant_id):
        return reverse("parohija:switch", kwargs={"tenant_id": tenant_id})

    def test_anonymous_redirects_to_login(self):
        r = self.client.post(self.url(self.tenant_a.pk))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_get_not_allowed(self):
        self.client.force_login(self.superuser)
        r = self.client.get(self.url(self.tenant_a.pk))
        self.assertEqual(r.status_code, 405)

    def test_superuser_can_switch_to_any_active(self):
        self.client.force_login(self.superuser)
        r = self.client.post(self.url(self.tenant_b.pk))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.session[SESSION_TENANT_KEY], self.tenant_b.pk)

    def test_member_can_switch_to_own_tenant(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url(self.tenant_a.pk))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.session[SESSION_TENANT_KEY], self.tenant_a.pk)

    def test_non_member_forbidden(self):
        self.client.force_login(self.user)
        r = self.client.post(self.url(self.tenant_b.pk))
        self.assertEqual(r.status_code, 403)
        self.assertNotEqual(
            self.client.session.get(SESSION_TENANT_KEY), self.tenant_b.pk
        )

    def test_inactive_tenant_is_404(self):
        self.client.force_login(self.superuser)
        r = self.client.post(self.url(self.tenant_inactive.pk))
        self.assertEqual(r.status_code, 404)

    def test_unknown_tenant_is_404(self):
        self.client.force_login(self.superuser)
        r = self.client.post(self.url(999999))
        self.assertEqual(r.status_code, 404)

    def test_redirect_to_next_when_provided(self):
        self.client.force_login(self.superuser)
        r = self.client.post(self.url(self.tenant_b.pk), {"next": "/krstenja/"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "/krstenja/")
