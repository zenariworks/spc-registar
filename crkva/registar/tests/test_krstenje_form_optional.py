"""KrstenjeForm field optionality matches the model (#230).

`Krstenje.hram` and `Krstenje.svestenik` are nullable; they must also be
optional on the form, mirroring `dete`. Historical records may lack a known
priest or temple.
"""

# pylint: disable=missing-function-docstring

from django.test import SimpleTestCase, TestCase
from registar.forms.krstenje import KrstenjeForm
from registar.models import Krstenje


class KrstenjeModelBlankTests(SimpleTestCase):
    def test_hram_allows_blank(self):
        self.assertTrue(Krstenje._meta.get_field("hram").blank)

    def test_svestenik_allows_blank(self):
        self.assertTrue(Krstenje._meta.get_field("svestenik").blank)


class KrstenjeFormOptionalTests(TestCase):
    def test_hram_and_svestenik_optional_like_dete(self):
        form = KrstenjeForm()
        self.assertFalse(form.fields["hram"].required)
        self.assertFalse(form.fields["svestenik"].required)
        self.assertFalse(form.fields["dete"].required)
