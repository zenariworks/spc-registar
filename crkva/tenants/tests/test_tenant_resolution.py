"""Tenant resolution honours active membership state (#227).

A deactivated UserMembership must not auto-resolve to that parish, must be
evicted from the session if stale, and must never affect other parishes.
"""

# pylint: disable=missing-function-docstring

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from tenants.middleware import SESSION_TENANT_KEY, SessionTenantMiddleware
from tenants.models import Role, Tenant, UserMembership


class ResolveTenantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        # bulk_create bypasses TenantMixin.save() (no schema provisioning).
        Tenant.objects.bulk_create(
            [
                Tenant(
                    schema_name="test_tenant_res2",
                    naziv="Res2",
                    is_active=True,
                )
            ]
        )
        cls.tenant2 = Tenant.objects.get(schema_name="test_tenant_res2")
        cls.user = User.objects.create_user(username="resu", password="x")

    def _req(self, user, session=None):
        request = RequestFactory().get("/")
        request.user = user
        request.session = dict(session or {})
        return request

    def resolve(self, request):
        # _resolve_tenant now returns (tenant, membership); tests assert on the
        # resolved tenant (membership is the perm-cache seed, see #256).
        tenant, _membership = SessionTenantMiddleware._resolve_tenant(request)
        return tenant

    def test_active_membership_resolves_and_sets_session(self):
        UserMembership.objects.create(
            user=self.user, tenant=self.tenant2, role=Role.PREGLED
        )
        req = self._req(self.user)
        self.assertEqual(self.resolve(req), self.tenant2)
        self.assertEqual(req.session[SESSION_TENANT_KEY], self.tenant2.pk)

    def test_deactivated_membership_is_skipped(self):
        UserMembership.objects.create(
            user=self.user, tenant=self.tenant2, role=Role.PREGLED, is_active=False
        )
        # tenant2 is not the default, so it can only be reached via membership.
        self.assertNotEqual(self.resolve(self._req(self.user)), self.tenant2)

    def test_deactivated_membership_in_session_is_evicted(self):
        UserMembership.objects.create(
            user=self.user, tenant=self.tenant2, role=Role.PREGLED, is_active=False
        )
        req = self._req(self.user, {SESSION_TENANT_KEY: self.tenant2.pk})
        self.assertNotEqual(self.resolve(req), self.tenant2)
        self.assertNotIn(SESSION_TENANT_KEY, req.session)

    def test_active_membership_preferred_over_deactivated_one(self):
        UserMembership.objects.create(
            user=self.user, tenant=self.tenant, role=Role.PREGLED, is_active=False
        )
        UserMembership.objects.create(
            user=self.user, tenant=self.tenant2, role=Role.PREGLED, is_active=True
        )
        self.assertEqual(self.resolve(self._req(self.user)), self.tenant2)

    def test_superuser_session_tenant_honoured_without_membership(self):
        su = User.objects.create_superuser(
            username="resroot", password="x", email="r@t"
        )
        req = self._req(su, {SESSION_TENANT_KEY: self.tenant2.pk})
        self.assertEqual(self.resolve(req), self.tenant2)
