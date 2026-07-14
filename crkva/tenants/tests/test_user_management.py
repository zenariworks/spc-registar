"""Tests for admin user-management views (tenant-scoped)."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from tenants.models import Clanstvo, Uloga, Zakupac

User = get_user_model()


class UserManagementViewTests(TestCase):
    """Smoke tests for /parohija/users/ list, add, role-edit, deactivate."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Zakupac.objects.get(schema_name="test_tenant")
        # bulk_create bypasses the django-tenants schema-check on save()
        Zakupac.objects.bulk_create(
            [
                Zakupac(
                    schema_name="test_tenant_other",
                    naziv="Other",
                    is_active=True,
                )
            ]
        )
        cls.other_tenant = Zakupac.objects.get(schema_name="test_tenant_other")
        cls.admin = User.objects.create_user(username="adm", password="x")
        Clanstvo.objects.create(
            korisnik=cls.admin, parohija=cls.tenant, uloga=Uloga.ADMIN
        )
        cls.clerk = User.objects.create_user(username="kanc", password="x")
        Clanstvo.objects.create(
            korisnik=cls.clerk, parohija=cls.tenant, uloga=Uloga.KANCELARIJA
        )
        cls.foreign_admin = User.objects.create_user(username="other_adm", password="x")
        Clanstvo.objects.create(
            korisnik=cls.foreign_admin, parohija=cls.other_tenant, uloga=Uloga.ADMIN
        )
        cls.foreign_clerk = User.objects.create_user(
            username="other_kanc", password="x"
        )
        Clanstvo.objects.create(
            korisnik=cls.foreign_clerk,
            parohija=cls.other_tenant,
            uloga=Uloga.KANCELARIJA,
        )

    def setUp(self):
        self.client = Client()

    # ----- list -----

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(reverse("parohija:korisnici"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_non_admin_forbidden(self):
        self.client.force_login(self.clerk)
        r = self.client.get(reverse("parohija:korisnici"))
        self.assertEqual(r.status_code, 403)

    def test_admin_sees_only_their_tenants_users(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse("parohija:korisnici"))
        self.assertEqual(r.status_code, 200)
        usernames = [m.korisnik.username for m in r.context["memberships"]]
        self.assertIn("adm", usernames)
        self.assertIn("kanc", usernames)
        self.assertNotIn("other_adm", usernames)
        self.assertNotIn("other_kanc", usernames)

    # ----- add -----

    def test_admin_can_add_user(self):
        self.client.force_login(self.admin)
        before = User.objects.count()
        r = self.client.post(
            reverse("parohija:dodavanje"),
            {
                "username": "newuser",
                "password": "veryStrong!Pass1",
                "first_name": "",
                "last_name": "",
                "email": "",
                "role": Uloga.KANCELARIJA,
                "is_default": "on",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(User.objects.count(), before + 1)
        new_user = User.objects.get(username="newuser")
        m = Clanstvo.objects.get(korisnik=new_user)
        self.assertEqual(m.parohija_id, self.tenant.pk)
        self.assertEqual(m.uloga, Uloga.KANCELARIJA)

    def test_non_admin_cannot_add_user(self):
        self.client.force_login(self.clerk)
        r = self.client.post(
            reverse("parohija:dodavanje"),
            {
                "username": "nope",
                "password": "veryStrong!Pass1",
                "role": Uloga.PREGLED,
            },
        )
        self.assertEqual(r.status_code, 403)

    def test_existing_member_of_this_parish_rejected(self):
        # „kanc“ је већ члан ове парохије → грешка, без дупог чланства (#228).
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:dodavanje"),
            {"username": "kanc", "role": Uloga.PREGLED},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["form"].errors)
        self.assertEqual(
            Clanstvo.objects.filter(korisnik=self.clerk, parohija=self.tenant).count(),
            1,
        )

    def test_existing_user_added_to_current_parish(self):
        # Постојећи корисник из друге парохије се веже за ову — без новог налога.
        self.client.force_login(self.admin)
        before = User.objects.count()
        r = self.client.post(
            reverse("parohija:dodavanje"),
            {"username": "other_kanc", "role": Uloga.PREGLED},
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(User.objects.count(), before)
        self.assertTrue(
            Clanstvo.objects.filter(
                korisnik=self.foreign_clerk, parohija=self.tenant, uloga=Uloga.PREGLED
            ).exists()
        )
        self.assertTrue(
            Clanstvo.objects.filter(
                korisnik=self.foreign_clerk, parohija=self.other_tenant
            ).exists()
        )

    def test_existing_user_password_not_reset(self):
        # Admin једне парохије не сме да ресетује глобалну лозинку (#228).
        self.client.force_login(self.admin)
        old_hash = User.objects.get(username="other_kanc").password
        self.client.post(
            reverse("parohija:dodavanje"),
            {
                "username": "other_kanc",
                "password": "attackerNewPass!9",
                "role": Uloga.PREGLED,
            },
        )
        self.assertEqual(User.objects.get(username="other_kanc").password, old_hash)

    def test_new_user_requires_password(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:dodavanje"),
            {"username": "brandnew", "role": Uloga.PREGLED},
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("password", r.context["form"].errors)
        self.assertFalse(User.objects.filter(username="brandnew").exists())

    def test_setting_default_clears_previous_default(self):
        m_other = Clanstvo.objects.get(
            korisnik=self.foreign_clerk, parohija=self.other_tenant
        )
        m_other.is_default = True
        m_other.save()
        self.client.force_login(self.admin)
        self.client.post(
            reverse("parohija:dodavanje"),
            {"username": "other_kanc", "role": Uloga.PREGLED, "is_default": "on"},
        )
        m_other.refresh_from_db()
        self.assertFalse(m_other.is_default)
        self.assertTrue(
            Clanstvo.objects.get(
                korisnik=self.foreign_clerk, parohija=self.tenant
            ).is_default
        )

    # ----- edit role -----

    def test_admin_can_change_role(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:izmena_uloge", kwargs={"user_id": self.clerk.pk}),
            {"role": Uloga.PREGLED},
        )
        self.assertEqual(r.status_code, 302)
        m = Clanstvo.objects.get(korisnik=self.clerk, parohija=self.tenant)
        self.assertEqual(m.uloga, Uloga.PREGLED)

    def test_admin_cannot_edit_other_tenants_user(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:izmena_uloge", kwargs={"user_id": self.foreign_clerk.pk}),
            {"role": Uloga.PREGLED},
        )
        self.assertEqual(r.status_code, 404)
        m = Clanstvo.objects.get(
            korisnik=self.foreign_clerk, parohija=self.other_tenant
        )
        self.assertEqual(m.uloga, Uloga.KANCELARIJA)  # unchanged

    # ----- deactivate -----

    def test_admin_can_deactivate_membership_not_global_user(self):
        # Deactivation toggles the *membership*, never the shared User row.
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:deaktiviranje", kwargs={"user_id": self.clerk.pk}),
        )
        self.assertEqual(r.status_code, 302)
        membership = Clanstvo.objects.get(korisnik=self.clerk, parohija=self.tenant)
        self.assertFalse(membership.is_active)
        self.clerk.refresh_from_db()
        self.assertTrue(self.clerk.is_active)  # global account untouched (#227)

    def test_deactivation_does_not_leak_into_other_parish(self):
        # A clerk who belongs to two parishes: deactivating membership in the
        # active parish must leave the membership in the other parish alone.
        Clanstvo.objects.create(
            korisnik=self.clerk, parohija=self.other_tenant, uloga=Uloga.KANCELARIJA
        )
        self.client.force_login(self.admin)
        self.client.post(
            reverse("parohija:deaktiviranje", kwargs={"user_id": self.clerk.pk}),
        )
        here = Clanstvo.objects.get(korisnik=self.clerk, parohija=self.tenant)
        there = Clanstvo.objects.get(korisnik=self.clerk, parohija=self.other_tenant)
        self.assertFalse(here.is_active)
        self.assertTrue(there.is_active)  # other parish unaffected (#227)

    def test_admin_can_reactivate_membership(self):
        membership = Clanstvo.objects.get(korisnik=self.clerk, parohija=self.tenant)
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        self.client.force_login(self.admin)
        self.client.post(
            reverse("parohija:deaktiviranje", kwargs={"user_id": self.clerk.pk}),
        )
        membership.refresh_from_db()
        self.assertTrue(membership.is_active)

    def test_admin_cannot_deactivate_self(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse("parohija:deaktiviranje", kwargs={"user_id": self.admin.pk}),
        )
        self.assertEqual(r.status_code, 302)
        membership = Clanstvo.objects.get(korisnik=self.admin, parohija=self.tenant)
        self.assertTrue(membership.is_active)

    def test_admin_cannot_deactivate_other_tenants_user(self):
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse(
                "parohija:deaktiviranje", kwargs={"user_id": self.foreign_clerk.pk}
            ),
        )
        self.assertEqual(r.status_code, 404)
        membership = Clanstvo.objects.get(
            korisnik=self.foreign_clerk, parohija=self.other_tenant
        )
        self.assertTrue(membership.is_active)
