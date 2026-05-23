"""Smoke test: select2 skin CSS is bundled and active on edit pages."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(COMPRESS_ENABLED=False)
class Select2SkinTestCase(TestCase):
    """Smoke checks for the select2 dropdown skin."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="x")
        self.client.force_login(self.user)

    def test_select2_skin_css_present_on_pages_with_select2(self):
        """The select2_skin.css link tag must appear on at least one page."""
        response = self.client.get(reverse("pocetna"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn(
            "select2_skin.css",
            html,
            "select2_skin.css must be referenced in base.html so the dropdown skin loads",
        )

    def test_select2_skin_css_overrides_known_classes(self):
        """The CSS file must target the key select2 classes we restyled."""
        import pathlib

        # Locate the bundled file via its real path
        css_path = pathlib.Path(
            "crkva/registar/static/registar/components/select2_skin.css"
        )
        text = css_path.read_text(encoding="utf-8")
        for selector in [
            ".select2-dropdown",
            ".select2-search--dropdown",
            ".select2-results__option",
            ".select2-results__option--highlighted",
        ]:
            self.assertIn(selector, text, f"missing rule for {selector}")
