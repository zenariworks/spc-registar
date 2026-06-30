"""Тестови за заједничке валидаторе форми (`registar.forms.validators`)."""

from django import forms
from django.test import SimpleTestCase
from registar.forms.validators import default_parohijan_off, validate_distinct_roles


class _RoleForm(forms.Form):
    """Минимална форма са три улоге за проверу валидатора."""

    a = forms.CharField(required=False)
    b = forms.CharField(required=False)
    c = forms.CharField(required=False)


class ValidateDistinctRolesTest(SimpleTestCase):
    def _run(self, data):
        form = _RoleForm(data=data)
        form.is_valid()
        validate_distinct_roles(form, ("a", "b", "c"))
        return form

    def test_dupli_dodaje_gresku_na_drugo_polje(self):
        form = self._run({"a": "Pera", "b": "Pera", "c": ""})
        self.assertIn("b", form.errors)
        self.assertNotIn("a", form.errors)
        self.assertIn("и a и b", form.errors["b"][0])

    def test_razliciti_nema_greske(self):
        form = self._run({"a": "Pera", "b": "Mika", "c": "Zika"})
        self.assertEqual(form.errors, {})

    def test_prazne_vrednosti_se_ignorisu(self):
        form = self._run({"a": "", "b": "", "c": "Pera"})
        self.assertEqual(form.errors, {})

    def test_svi_parovi_se_proveravaju(self):
        form = self._run({"a": "Pera", "b": "Mika", "c": "Pera"})
        # a==c → грешка иде на друго поље пара (c)
        self.assertIn("c", form.errors)
        self.assertIn("и a и c", form.errors["c"][0])


class DefaultParohijanOffTest(SimpleTestCase):
    def test_postavlja_atribut_na_data_polja(self):
        form = _RoleForm()
        default_parohijan_off(form, ("a", "c"))
        self.assertEqual(
            form.fields["a"].widget.attrs["data-osoba-parohijan-default"], "0"
        )
        self.assertEqual(
            form.fields["c"].widget.attrs["data-osoba-parohijan-default"], "0"
        )
        self.assertNotIn("data-osoba-parohijan-default", form.fields["b"].widget.attrs)
