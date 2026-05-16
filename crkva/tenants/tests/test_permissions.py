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
            {"ime": "Иван", "prezime": "Тест", "pol": "M"},
        )
        self.assertEqual(r.status_code, 403)

    def test_clerk_can_quick_add_osoba(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            "/api/brzi-unos-osobe/",
            {"ime": "Иван", "prezime": "Тест", "pol": "M"},
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
