"""Tests for tenants.permissions: role-based write gating."""

# pylint: disable=missing-function-docstring  # test names describe intent

from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase
from tenants.models import Role, Tenant, UserMembership
from tenants.permissions import (
    DOMACINSTVO,
    KRSTENJE,
    OSOBA,
    SVESTENIK,
    VENCANJE,
    can_edit,
)


class CanEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.superuser = User.objects.create_superuser(
            username="root", password="x", email="root@test"
        )
        cls.admin = User.objects.create_user(username="adm", password="x")
        UserMembership.objects.create(
            user=cls.admin, tenant=cls.tenant, role=Role.ADMIN
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.priest = User.objects.create_user(username="svest", password="x")
        UserMembership.objects.create(
            user=cls.priest, tenant=cls.tenant, role=Role.SVESTENSTVO
        )
        cls.viewer = User.objects.create_user(username="view", password="x")
        UserMembership.objects.create(
            user=cls.viewer, tenant=cls.tenant, role=Role.PREGLED
        )
        cls.stranger = User.objects.create_user(username="nope", password="x")

    def test_anonymous_cannot_edit_anything(self):
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK]:
            self.assertFalse(can_edit(AnonymousUser(), self.tenant, resource))

    def test_superuser_can_edit_everything(self):
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK]:
            self.assertTrue(can_edit(self.superuser, self.tenant, resource))

    def test_admin_role_can_edit_everything(self):
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK]:
            self.assertTrue(can_edit(self.admin, self.tenant, resource))

    def test_kancelarija_edits_data_but_not_svestenik(self):
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE]:
            self.assertTrue(
                can_edit(self.clerk, self.tenant, resource),
                f"clerk should edit {resource}",
            )
        self.assertFalse(can_edit(self.clerk, self.tenant, SVESTENIK))

    def test_svestenstvo_edits_only_svestenik(self):
        self.assertTrue(can_edit(self.priest, self.tenant, SVESTENIK))
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE]:
            self.assertFalse(
                can_edit(self.priest, self.tenant, resource),
                f"priest should NOT edit {resource}",
            )

    def test_pregled_cannot_edit_anything(self):
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK]:
            self.assertFalse(can_edit(self.viewer, self.tenant, resource))

    def test_user_without_membership_cannot_edit(self):
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK]:
            self.assertFalse(can_edit(self.stranger, self.tenant, resource))

    def test_no_tenant_means_no_edit(self):
        self.assertFalse(can_edit(self.admin, None, OSOBA))

    def test_deactivated_membership_cannot_edit(self):
        # A clerk normally edits osoba; deactivating the membership revokes it
        # without touching the shared User account (#227).
        m = UserMembership.objects.get(user=self.clerk, tenant=self.tenant)
        m.is_active = False
        m.save(update_fields=["is_active"])
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE]:
            self.assertFalse(can_edit(self.clerk, self.tenant, resource))
        self.assertTrue(self.clerk.is_active)  # global account untouched

    def test_superuser_unaffected_by_membership_state(self):
        # Superusers have no membership row at all and still edit everything.
        for resource in [OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK]:
            self.assertTrue(can_edit(self.superuser, self.tenant, resource))


class GatedViewTests(TestCase):
    """End-to-end: GET /unos/parohijan/ returns 403 for non-permitted roles."""

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

    def test_clerk_can_open_parohijan_form(self):
        self.client.force_login(self.clerk)
        r = self.client.get("/unos/parohijan/")
        self.assertEqual(r.status_code, 200)

    def test_priest_cannot_open_parohijan_form(self):
        self.client.force_login(self.priest)
        r = self.client.get("/unos/parohijan/")
        self.assertEqual(r.status_code, 403)

    def test_clerk_cannot_quick_add_osoba_via_priest_role_fail(self):
        # priest role isn't allowed to create osoba via brzi_unos_osobe
        self.client.force_login(self.priest)
        r = self.client.post(
            "/api/brzi-unos-osobe/",
            {"ime": "Иван", "prezime": "Тест", "pol": "М"},
        )
        self.assertEqual(r.status_code, 403)

    def test_clerk_can_quick_add_osoba(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            "/api/brzi-unos-osobe/",
            {"ime": "Иван", "prezime": "Тест", "pol": "М"},
        )
        self.assertEqual(r.status_code, 200)

    def test_anonymous_redirects_to_login(self):
        r = self.client.get("/unos/parohijan/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])


class ContextProcessorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def test_template_sees_can_edit_flags(self):
        from tenants.context_processors import current_tenant

        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.clerk
        request.tenant = self.tenant
        ctx = current_tenant(request)
        self.assertTrue(ctx["can_edit_osoba"])
        self.assertTrue(ctx["can_edit_krstenje"])
        self.assertFalse(ctx["can_edit_svestenik"])

    def test_context_processor_issues_single_membership_query(self):
        # Regression for #256: every can_edit_* flag + is_admin derive from a
        # single membership lookup, not one query per flag (was ~6 per render).
        # We count only queries hitting the membership table, because
        # django-tenants emits a "SET search_path" alongside each query in the
        # test harness which would otherwise inflate a raw query count.
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from tenants.context_processors import current_tenant

        factory = RequestFactory()
        request = factory.get("/")
        request.user = User.objects.get(pk=self.clerk.pk)  # cold per-request cache
        request.tenant = self.tenant
        with CaptureQueriesContext(connection) as captured:
            current_tenant(request)
        membership_queries = [
            q
            for q in captured.captured_queries
            if "tenants_user_membership" in q["sql"]
        ]
        self.assertEqual(
            len(membership_queries),
            1,
            "context processor must resolve the role in one membership query "
            f"(got {len(membership_queries)})",
        )

    def test_context_processor_superuser_needs_no_query(self):
        from tenants.context_processors import current_tenant

        su = User.objects.create_superuser(
            username="su256", password="x", email="su256@test"
        )
        factory = RequestFactory()
        request = factory.get("/")
        request.user = su
        request.tenant = self.tenant
        with self.assertNumQueries(0):
            ctx = current_tenant(request)
        self.assertTrue(ctx["can_edit_osoba"])
        self.assertTrue(ctx["is_tenant_admin"])


class MembershipPrimingTests(TestCase):
    """#256: the middleware's resolution membership primes the per-request
    permission cache, so the context processor/decorators re-query zero times.
    """

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="prime_kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def _membership_queries(self, fn):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as cap:
            fn()
        return [q for q in cap.captured_queries
                if "tenants_user_membership" in q["sql"]]

    def test_prime_makes_permission_checks_query_free(self):
        from tenants.permissions import (
            can_edit, is_tenant_admin, prime_tenant_permissions,
        )
        user = User.objects.get(pk=self.clerk.pk)  # fresh instance
        membership = UserMembership.objects.get(user=user, tenant=self.tenant)
        prime_tenant_permissions(user, self.tenant, membership)

        q = self._membership_queries(lambda: (
            can_edit(user, self.tenant, OSOBA),
            can_edit(user, self.tenant, SVESTENIK),
            is_tenant_admin(user, self.tenant),
        ))
        self.assertEqual(len(q), 0, "primed cache must avoid membership queries")
        self.assertTrue(can_edit(user, self.tenant, OSOBA))
        self.assertFalse(can_edit(user, self.tenant, SVESTENIK))
        self.assertFalse(is_tenant_admin(user, self.tenant))

    def test_middleware_resolution_primes_context_processor(self):
        from tenants.context_processors import current_tenant
        from tenants.middleware import SessionTenantMiddleware
        from tenants.permissions import prime_tenant_permissions

        request = RequestFactory().get("/")
        request.user = User.objects.get(pk=self.clerk.pk)
        request.session = {}

        def resolve_and_prime():
            tenant, membership = SessionTenantMiddleware._resolve_tenant(request)
            request.tenant = tenant
            prime_tenant_permissions(request.user, tenant, membership)

        mw_q = self._membership_queries(resolve_and_prime)
        cp_q = self._membership_queries(lambda: current_tenant(request))

        self.assertLessEqual(len(mw_q), 1,
                             "resolution should cost at most one membership query")
        self.assertEqual(len(cp_q), 0,
                         "context processor must reuse the primed cache")
