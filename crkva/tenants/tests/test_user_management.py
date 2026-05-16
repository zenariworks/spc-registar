"""Tests for admin user-management views (tenant-scoped)."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class UserManagementViewTests(TestCase):
    """Smoke tests for /tenant/users/ list, add, role-edit, deactivate."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        # bulk_create bypasses the django-tenants schema-check on save()
        Tenant.objects.bulk_create(
            [
                Tenant(
                    schema_name="test_tenant_other",
                    naziv="Other",
                    parohija_naziv="Other",
                    is_active=True,
                )
            ]
        )
        cls.other_tenant = Tenant.objects.get(schema_name="test_tenant_other")
        cls.admin = User.objects.create_user(username="adm", password="x")
        UserMembership.objects.create(
            user=cls.admin, tenant=cls.tenant, role=Role.ADMIN
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.foreign_admin = User.objects.create_user(username="other_adm", password="x")
        UserMembership.objects.create(
            user=cls.foreign_admin, tenant=cls.other_tenant, role=Role.ADMIN
        )
        cls.foreign_clerk = User.objects.create_user(
            username="other_kanc", password="x"
        )
        UserMembership.objects.create(
            user=cls.foreign_clerk, tenant=cls.other_tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()

    # ----- list -----

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(reverse("tenants:user_list"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_non_admin_forbidden(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("tenants:user_list"))
        self.assertEqual(r.status_code, 403)

    def test_admin_sees_only_their_tenants_users(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("tenants:user_list"))
        self.assertEqual(r.status_code, 200)
        usernames = [m.user.username for m in r.context["memberships"]]
        self.assertIn("adm", usernames)
        self.assertIn("kanc", usernames)
        self.assertNotIn("other_adm", usernames)
        self.assertNotIn("other_kanc", usernames)

    # ----- add -----

    def test_admin_can_add_user(self):
        self.client.force_login(self.admin)
        before = User.objects.count()
        r = self.client.post(
            reverse("tenants:user_add"),
            {
                "username": "newuser",
                "password": "veryStrong!Pass1",
                "first_name": "",
                "last_name": "",
                "email": "",
                "role": Role.KANCELARIJA,
                "is_default": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(User.objects.count(), before + 1)
        new_user = User.objects.get(username="newuser")
        m = UserMembership.objects.get(user=new_user)
        self.assertEqual(m.tenant_id, self.tenant.pk)
        self.assertEqual(m.role, Role.KANCELARIJA)

    def test_non_admin_cannot_add_user(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            reverse("tenants:user_add"),
            {
                "username": "nope",
                "password": "veryStrong!Pass1",
                "role": Role.PREGLED,
            },
        )
        self.assertEqual(r.status_code, 403)

    def test_duplicate_username_rejected(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("tenants:user_add"),
            {
                "username": "kanc",  # already exists
                "password": "veryStrong!Pass1",
                "role": Role.PREGLED,
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)

    # ----- edit role -----

    def test_admin_can_change_role(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("tenants:user_edit_role", kwargs={"user_id": self.clerk.pk}),
            {"role": Role.PREGLED},
        )
        self.assertEqual(r.status_code, 302)
        m = UserMembership.objects.get(user=self.clerk, tenant=self.tenant)
        self.assertEqual(m.role, Role.PREGLED)

    def test_admin_cannot_edit_other_tenants_user(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse(
                "tenants:user_edit_role", kwargs={"user_id": self.foreign_clerk.pk}
            ),
            {"role": Role.PREGLED},
        )
        self.assertEqual(r.status_code, 404)
        m = UserMembership.objects.get(
            user=self.foreign_clerk, tenant=self.other_tenant
        )
        self.assertEqual(m.role, Role.KANCELARIJA)  # unchanged

    # ----- deactivate -----

    def test_admin_can_deactivate_user(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("tenants:user_deactivate", kwargs={"user_id": self.clerk.pk}),
        )
        self.assertEqual(r.status_code, 302)
        self.clerk.refresh_from_db()
        self.assertFalse(self.clerk.is_active)

    def test_admin_cannot_deactivate_self(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("tenants:user_deactivate", kwargs={"user_id": self.admin.pk}),
        )
        self.assertEqual(r.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_cannot_deactivate_other_tenants_user(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse(
                "tenants:user_deactivate", kwargs={"user_id": self.foreign_clerk.pk}
            ),
        )
        self.assertEqual(r.status_code, 404)
        self.foreign_clerk.refresh_from_db()
        self.assertTrue(self.foreign_clerk.is_active)
