"""Tests for the script-aware select2 mixin."""

from django.test import TestCase
from registar.forms.select2 import ScriptAwareModelSelect2Widget
from registar.models import Osoba


class ScriptAwareSelect2WidgetTest(TestCase):
    """The widget should match Latin queries against Cyrillic data and vice versa."""

    @classmethod
    def setUpTestData(cls):
        Osoba.objects.create(ime="Марко", prezime="Марковић")
        Osoba.objects.create(ime="Ана", prezime="Аћимовић")
        Osoba.objects.create(ime="Бошко", prezime="Бошковић")

    def _build_widget(self):
        widget = ScriptAwareModelSelect2Widget(
            model=Osoba,
            search_fields=["ime__icontains", "prezime__icontains"],
        )
        return widget

    def test_latin_query_matches_cyrillic_record(self):
        widget = self._build_widget()
        qs = widget.filter_queryset(
            request=None, term="Marko", queryset=Osoba.objects.all()
        )
        names = list(qs.values_list("ime", "prezime"))
        self.assertIn(("Марко", "Марковић"), names)

    def test_cyrillic_query_matches_cyrillic_record(self):
        """A Cyrillic search term returns the matching Cyrillic record."""
        widget = self._build_widget()
        qs = widget.filter_queryset(
            request=None, term="Марко", queryset=Osoba.objects.all()
        )
        self.assertEqual(qs.count(), 1)

    def test_empty_term_returns_full_queryset(self):
        """Empty search term yields the full queryset (suggestions on open)."""
        widget = self._build_widget()
        qs = widget.filter_queryset(request=None, term="", queryset=Osoba.objects.all())
        self.assertEqual(qs.count(), 3)

    def test_minimum_input_length_is_zero_so_suggestions_show_on_open(self):
        widget = self._build_widget()
        attrs = widget.build_attrs({})
        self.assertEqual(attrs.get("data-minimum-input-length"), 0)

    def test_latin_partial_matches_cyrillic(self):
        """Partial Latin input matches the Cyrillic prefix it transliterates to."""
        widget = self._build_widget()
        qs = widget.filter_queryset(
            request=None, term="Bo", queryset=Osoba.objects.all()
        )
        names = [p.ime for p in qs]
        self.assertIn("Бошко", names)
