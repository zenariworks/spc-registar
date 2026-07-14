"""Tests for the self-edit user profile view."""

# pylint: disable=missing-function-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class ProfileViewTests(TestCase):
    """Smoke tests for /parohija/profile/ info + password change."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="alice", password="oldpass123!", email="alice@old.test"
        )

    def setUp(self):
        self.client = Client()

    def url(self):
        return reverse("parohija:profil")

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 302)
        self.assertIn("/prijava/", r["Location"])

    def test_get_returns_form(self):
        self.client.force_login(self.user)
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "registar/profile.html")
        self.assertIn("info_form", r.context)
        self.assertIn("password_form", r.context)

    def test_save_info_updates_user(self):
        self.client.force_login(self.user)
        r = self.client.post(
            self.url(),
            {
                "action": "info",
                "first_name": "Алиса",
                "last_name": "Тест",
                "email": "alice@new.test",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Алиса")
        self.assertEqual(self.user.last_name, "Тест")
        self.assertEqual(self.user.email, "alice@new.test")

    def test_change_password_with_correct_old_password(self):
        self.client.force_login(self.user)
        r = self.client.post(
            self.url(),
            {
                "action": "password",
                "old_password": "oldpass123!",
                "new_password1": "newpass456!",
                "new_password2": "newpass456!",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456!"))

    def test_change_password_with_wrong_old_rejects(self):
        self.client.force_login(self.user)
        r = self.client.post(
            self.url(),
            {
                "action": "password",
                "old_password": "WRONG",
                "new_password1": "newpass456!",
                "new_password2": "newpass456!",
            },
        )
        self.assertEqual(r.status_code, 200)  # re-renders with errors
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpass123!"))

    def test_change_password_mismatched_new_passwords(self):
        self.client.force_login(self.user)
        r = self.client.post(
            self.url(),
            {
                "action": "password",
                "old_password": "oldpass123!",
                "new_password1": "newpass456!",
                "new_password2": "different!",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpass123!"))

    def test_change_password_keeps_user_logged_in(self):
        self.client.force_login(self.user)
        self.client.post(
            self.url(),
            {
                "action": "password",
                "old_password": "oldpass123!",
                "new_password1": "newpass456!",
                "new_password2": "newpass456!",
            },
        )
        # subsequent GET to a login_required view should still work
        r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
