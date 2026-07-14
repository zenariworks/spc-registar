"""Безбедносни уговор `markiraj` филтера (#375).

`markiraj` се у шаблонима користи као `{{ value|markiraj:upit|safe }}` — `|safe`
искључује аутоескејп, па филтер мора да врати већ ескејповану вредност на
СВАКОМ излазу, укључујући празан упит (подразумевано стање сваке списак-стране,
`upit=""`). Иначе се сирово име из базе рендерује неескејповано → складиштени XSS.
"""

from django.template import Context, Template
from django.test import SimpleTestCase
from django.utils.safestring import SafeString
from registar.templatetags.marker_filter import markiraj

XSS = "<img src=x onerror=alert(1)>"


class MarkirajEscapeContractTests(SimpleTestCase):
    def test_empty_query_escapes(self):
        """Празан упит: вредност мора бити ескејпована и safe."""
        out = markiraj(XSS, "")
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img", out)
        self.assertIsInstance(out, SafeString)

    def test_none_query_escapes(self):
        """`upit=None` иде истом граном као празан упит."""
        out = markiraj(XSS, None)
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img", out)

    def test_whitespace_query_no_terms_escapes(self):
        """Упит без стварних термина (само размаци): и даље ескејповано."""
        out = markiraj(XSS, "   ")
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img", out)

    def test_none_value_empty_query(self):
        """`value=None` враћа празан стринг, не 'None'."""
        self.assertEqual(markiraj(None, ""), "")

    def test_highlight_path_still_escapes_nonmatch(self):
        """Кад има погодака: HTML у вредности се и даље ескејпује, поготак истиче."""
        out = markiraj("<b>Ана</b>", "Ана")
        self.assertNotIn("<b>", out)
        self.assertIn("peachpuff", out)
        self.assertIn("Ана", out)

    def test_safe_filter_after_markiraj_keeps_escaped(self):
        """Продукциони пут: `{{ v|markiraj:upit|safe }}` са празним упитом не сме да XSS-ује."""
        tpl = Template("{% load marker_filter %}{{ v|markiraj:upit|safe }}")
        rendered = tpl.render(Context({"v": XSS, "upit": ""}))
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;img", rendered)
