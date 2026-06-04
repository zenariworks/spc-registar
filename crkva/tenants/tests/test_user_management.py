"""Tests for admin user-management views (tenant-scoped)."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class UserManagementViewTests(TestCase):
    """Smoke tests for /parohija/users/ list, add, role-edit, deactivate."""

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
        r = self.client.get(reverse("parohija:user_list"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_non_admin_forbidden(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("parohija:user_list"))
        self.assertEqual(r.status_code, 403)

    def test_admin_sees_only_their_tenants_users(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("parohija:user_list"))
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
            reverse("parohija:user_add"),
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
            reverse("parohija:user_add"),
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
            reverse("parohija:user_add"),
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
            reverse("parohija:user_edit_role", kwargs={"user_id": self.clerk.pk}),
            {"role": Role.PREGLED},
        )
        self.assertEqual(r.status_code, 302)
        m = UserMembership.objects.get(user=self.clerk, tenant=self.tenant)
        self.assertEqual(m.role, Role.PREGLED)

    def test_admin_cannot_edit_other_tenants_user(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse(
                "parohija:user_edit_role", kwargs={"user_id": self.foreign_clerk.pk}
            ),
            {"role": Role.PREGLED},
        )
        self.assertEqual(r.status_code, 404)
        m = UserMembership.objects.get(
            user=self.foreign_clerk, tenant=self.other_tenant
        )
        self.assertEqual(m.role, Role.KANCELARIJA)  # unchanged

    # ----- deactivate -----

    def test_admin_can_deactivate_membership_not_global_user(self):
        # Deactivation toggles the *membership*, never the shared User row.
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:user_deactivate", kwargs={"user_id": self.clerk.pk}),
        )
        self.assertEqual(r.status_code, 302)
        membership = UserMembership.objects.get(
            user=self.clerk, tenant=self.tenant
        )
        self.assertFalse(membership.is_active)
        self.clerk.refresh_from_db()
        self.assertTrue(self.clerk.is_active)  # global account untouched (#227)

    def test_deactivation_does_not_leak_into_other_parish(self):
        # A clerk who belongs to two parishes: deactivating membership in the
        # active parish must leave the membership in the other parish alone.
        UserMembership.objects.create(
            user=self.clerk, tenant=self.other_tenant, role=Role.KANCELARIJA
        )
        self.client.force_login(self.admin)
        self.client.post(
            reverse("parohija:user_deactivate", kwargs={"user_id": self.clerk.pk}),
        )
        here = UserMembership.objects.get(user=self.clerk, tenant=self.tenant)
        there = UserMembership.objects.get(user=self.clerk, tenant=self.other_tenant)
        self.assertFalse(here.is_active)
        self.assertTrue(there.is_active)  # other parish unaffected (#227)

    def test_admin_can_reactivate_membership(self):
        membership = UserMembership.objects.get(user=self.clerk, tenant=self.tenant)
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        self.client.force_login(self.admin)
        self.client.post(
            reverse("parohija:user_deactivate", kwargs={"user_id": self.clerk.pk}),
        )
        membership.refresh_from_db()
        self.assertTrue(membership.is_active)

    def test_admin_cannot_deactivate_self(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:user_deactivate", kwargs={"user_id": self.admin.pk}),
        )
        self.assertEqual(r.status_code, 302)
        membership = UserMembership.objects.get(user=self.admin, tenant=self.tenant)
        self.assertTrue(membership.is_active)

    def test_admin_cannot_deactivate_other_tenants_user(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse(
                "parohija:user_deactivate", kwargs={"user_id": self.foreign_clerk.pk}
            ),
        )
        self.assertEqual(r.status_code, 404)
        membership = UserMembership.objects.get(
            user=self.foreign_clerk, tenant=self.other_tenant
        )
        self.assertTrue(membership.is_active)
