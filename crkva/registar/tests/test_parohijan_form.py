"""Валидациони smoke тестови за ``ParohijanForm`` (#304).

Домен парохијана се интензивно користи, а форма до сада није имала
директан тест валидације. Покривамо минималан валидан унос, обавезна
поља и tenant-свесно парсирање телефона.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.test import TestCase
from registar.forms.parohijan import ParohijanForm


class ParohijanFormTests(TestCase):
    def test_minimal_valid(self):
        form = ParohijanForm(data={"ime": "Петар", "prezime": "Петровић"})
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_ime_prezime_required(self):
        form = ParohijanForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("ime", form.errors)
        self.assertIn("prezime", form.errors)

    def test_phone_parsed_with_tenant_region(self):
        form = ParohijanForm(
            data={"ime": "Ана", "prezime": "Анић", "tel_mobilni": "061 234 5678"}
        )
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data["tel_mobilni"].country_code, 381)
