"""Tests for gender-filtered Osoba select2 lookups.

When a clerk picks an Osoba for a role with an implied gender (father,
mother, etc.) the typeahead should only suggest people of that gender.
``pol=None`` is treated leniently — uncategorised legacy rows surface in
both male and female lookups.
"""

import re

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from registar.forms.krstenje_form import FemaleOsobaSelect2Widget as KrstFemale
from registar.forms.krstenje_form import KrstenjeForm
from registar.forms.krstenje_form import MaleOsobaSelect2Widget as KrstMale
from registar.forms.krstenje_form import OsobaSelect2Widget as KrstUnfiltered
from registar.forms.vencanje_form import FemaleOsobaSelect2Widget as VencFemale
from registar.forms.vencanje_form import MaleOsobaSelect2Widget as VencMale
from registar.forms.vencanje_form import VencanjeForm
from registar.models import Osoba

FIELD_ID_RE = re.compile(
    r'<select[^>]*name="(?P<name>[a-z_]+)"[^>]*data-field_id="(?P<fid>[^"]+)"'
)
DEFAULT_POL_RE = re.compile(
    r'<select[^>]*name="(?P<name>[a-z_]+)"[^>]*data-osoba-default-pol="(?P<pol>[МЖ])"'
)


def _extract_field_ids(html: str) -> dict[str, str]:
    """Return ``{field_name: signed field_id}`` for every rendered <select>.

    The ``data-field_id`` attribute may appear before or after ``name=`` so we
    rescan with name-first and field-id-first patterns and merge.
    """
    out = {}
    for m in FIELD_ID_RE.finditer(html):
        out[m.group("name")] = m.group("fid")
    # Also catch order: data-field_id="..." ... name="..."
    alt = re.compile(
        r'<select[^>]*data-field_id="(?P<fid>[^"]+)"[^>]*name="(?P<name>[a-z_]+)"'
    )
    for m in alt.finditer(html):
        out.setdefault(m.group("name"), m.group("fid"))
    return out


# ---------------------------------------------------------------------------
# Widget-level filtering (queryset)
# ---------------------------------------------------------------------------


class WidgetQuerysetFilteringTests(TestCase):
    """Unit-level: ``get_queryset()`` enforces the gender restriction."""

    @classmethod
    def setUpTestData(cls):
        cls.male = Osoba.objects.create(ime="Марко", prezime="Марковић", pol="М")
        cls.female = Osoba.objects.create(ime="Марија", prezime="Марковић", pol="Ж")
        cls.legacy = Osoba.objects.create(ime="Стеван", prezime="Стевановић", pol=None)

    def test_male_widget_excludes_female(self):
        qs = KrstMale().get_queryset()
        self.assertIn(self.male, qs)
        self.assertNotIn(self.female, qs)

    def test_female_widget_excludes_male(self):
        qs = KrstFemale().get_queryset()
        self.assertIn(self.female, qs)
        self.assertNotIn(self.male, qs)

    def test_pol_none_passes_through_both_filters(self):
        """An Osoba with pol=None should appear in BOTH male and female lookups."""
        self.assertIn(self.legacy, KrstMale().get_queryset())
        self.assertIn(self.legacy, KrstFemale().get_queryset())
        self.assertIn(self.legacy, VencMale().get_queryset())
        self.assertIn(self.legacy, VencFemale().get_queryset())

    def test_unfiltered_widget_keeps_everyone(self):
        qs = KrstUnfiltered().get_queryset()
        self.assertIn(self.male, qs)
        self.assertIn(self.female, qs)
        self.assertIn(self.legacy, qs)


# ---------------------------------------------------------------------------
# Form Meta.widgets wiring
# ---------------------------------------------------------------------------


class FormWidgetWiringTests(TestCase):
    """Each gendered field is bound to the right Male/Female widget."""

    def test_krstenje_otac_uses_male_widget(self):
        self.assertIsInstance(KrstenjeForm().fields["otac"].widget, KrstMale)

    def test_krstenje_majka_uses_female_widget(self):
        self.assertIsInstance(KrstenjeForm().fields["majka"].widget, KrstFemale)

    def test_krstenje_dete_is_unfiltered(self):
        widget = KrstenjeForm().fields["dete"].widget
        self.assertIsInstance(widget, KrstUnfiltered)
        self.assertNotIsInstance(widget, KrstMale)
        self.assertNotIsInstance(widget, KrstFemale)

    def test_krstenje_kum_is_unfiltered(self):
        widget = KrstenjeForm().fields["kum"].widget
        self.assertIsInstance(widget, KrstUnfiltered)
        self.assertNotIsInstance(widget, KrstMale)
        self.assertNotIsInstance(widget, KrstFemale)

    def test_vencanje_male_fields(self):
        form = VencanjeForm()
        for name in ("zenik", "svekar", "tast", "stari_svat"):
            self.assertIsInstance(
                form.fields[name].widget,
                VencMale,
                msg=f"{name!r} must use MaleOsobaSelect2Widget",
            )

    def test_vencanje_female_fields(self):
        form = VencanjeForm()
        for name in ("nevesta", "svekrva", "tasta"):
            self.assertIsInstance(
                form.fields[name].widget,
                VencFemale,
                msg=f"{name!r} must use FemaleOsobaSelect2Widget",
            )

    def test_vencanje_kum_is_unfiltered(self):
        widget = VencanjeForm().fields["kum"].widget
        self.assertNotIsInstance(widget, VencMale)
        self.assertNotIsInstance(widget, VencFemale)


# ---------------------------------------------------------------------------
# Rendered HTML carries the data-osoba-default-pol attribute
# ---------------------------------------------------------------------------


class RenderedDataAttributeTests(TestCase):
    """The data-osoba-default-pol attribute drives the modal's Pol toggle."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="dataattr", email="t@x.test", password="x"
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _get(self, url_name):
        r = self.client.get(reverse(url_name))
        self.assertEqual(r.status_code, 200)
        return r.content.decode("utf-8")

    def test_krstenje_majka_carries_female_default_pol(self):
        html = self._get("unos_krstenja")
        self.assertRegex(
            html,
            r'<select[^>]*name="majka"[^>]*data-osoba-default-pol="Ж"',
        )

    def test_krstenje_otac_carries_male_default_pol(self):
        html = self._get("unos_krstenja")
        self.assertRegex(
            html,
            r'<select[^>]*name="otac"[^>]*data-osoba-default-pol="М"',
        )

    def test_krstenje_kum_has_no_default_pol(self):
        html = self._get("unos_krstenja")
        # Find the kum <select> tag and assert no data-osoba-default-pol on it.
        m = re.search(r'<select[^>]*name="kum"[^>]*>', html)
        self.assertIsNotNone(m, "kum <select> not rendered")
        self.assertNotIn("data-osoba-default-pol", m.group(0))

    def test_krstenje_dete_has_no_default_pol(self):
        html = self._get("unos_krstenja")
        m = re.search(r'<select[^>]*name="dete"[^>]*>', html)
        self.assertIsNotNone(m, "dete <select> not rendered")
        self.assertNotIn("data-osoba-default-pol", m.group(0))

    def test_vencanje_gendered_fields_carry_default_pol(self):
        html = self._get("unos_vencanja")
        expected = {
            "zenik": "М",
            "svekar": "М",
            "tast": "М",
            "stari_svat": "М",
            "nevesta": "Ж",
            "svekrva": "Ж",
            "tasta": "Ж",
        }
        for name, pol in expected.items():
            self.assertRegex(
                html,
                rf'<select[^>]*name="{name}"[^>]*data-osoba-default-pol="{pol}"',
                msg=f"{name!r} must carry data-osoba-default-pol={pol!r}",
            )

    def test_vencanje_kum_has_no_default_pol(self):
        html = self._get("unos_vencanja")
        m = re.search(r'<select[^>]*name="kum"[^>]*>', html)
        self.assertIsNotNone(m, "kum <select> not rendered")
        self.assertNotIn("data-osoba-default-pol", m.group(0))


# ---------------------------------------------------------------------------
# Live AJAX endpoint (auto.json) honours the gender filter
# ---------------------------------------------------------------------------


class Select2AjaxGenderFilterTests(TestCase):
    """Probe ``/select2/fields/auto.json`` with field_ids harvested from the
    rendered form page and assert each lookup returns only gender-appropriate
    Osoba rows."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="ajaxgender", email="t@x.test", password="x"
        )
        cls.male = Osoba.objects.create(ime="Марко", prezime="Тест", pol="М")
        cls.female = Osoba.objects.create(ime="Марија", prezime="Тест", pol="Ж")
        cls.legacy = Osoba.objects.create(ime="Стеван", prezime="Тест", pol=None)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def _field_ids(self, url_name):
        r = self.client.get(reverse(url_name))
        self.assertEqual(r.status_code, 200)
        return _extract_field_ids(r.content.decode("utf-8"))

    def _ajax_ids(self, fid, term=""):
        url = reverse("django_select2:auto-json")
        r = self.client.get(url, {"field_id": fid, "term": term})
        self.assertEqual(r.status_code, 200, msg=r.content[:200])
        return {row["id"] for row in r.json().get("results", [])}

    # --- Krstenje --------------------------------------------------------

    def test_majka_widget_filters_female_osoba(self):
        ids = self._field_ids("unos_krstenja")
        self.assertIn("majka", ids, msg=f"available: {list(ids)}")
        results = self._ajax_ids(ids["majka"], term="Тест")
        self.assertIn(self.female.pk, results)
        self.assertIn(self.legacy.pk, results)
        self.assertNotIn(self.male.pk, results)

    def test_otac_widget_filters_male_osoba(self):
        ids = self._field_ids("unos_krstenja")
        results = self._ajax_ids(ids["otac"], term="Тест")
        self.assertIn(self.male.pk, results)
        self.assertIn(self.legacy.pk, results)
        self.assertNotIn(self.female.pk, results)

    def test_dete_widget_has_no_gender_filter(self):
        ids = self._field_ids("unos_krstenja")
        results = self._ajax_ids(ids["dete"], term="Тест")
        self.assertEqual(
            {self.male.pk, self.female.pk, self.legacy.pk},
            results & {self.male.pk, self.female.pk, self.legacy.pk},
        )

    def test_kum_widget_has_no_gender_filter(self):
        """/unos/krstenje/ kum field is unfiltered — both sexes show up."""
        ids = self._field_ids("unos_krstenja")
        results = self._ajax_ids(ids["kum"], term="Тест")
        for o in (self.male, self.female, self.legacy):
            self.assertIn(o.pk, results, msg=f"{o.ime} missing from kum lookup")

    # --- Vencanje --------------------------------------------------------

    def test_zenik_widget_filters_male(self):
        ids = self._field_ids("unos_vencanja")
        results = self._ajax_ids(ids["zenik"], term="Тест")
        self.assertIn(self.male.pk, results)
        self.assertNotIn(self.female.pk, results)

    def test_nevesta_widget_filters_female(self):
        ids = self._field_ids("unos_vencanja")
        results = self._ajax_ids(ids["nevesta"], term="Тест")
        self.assertIn(self.female.pk, results)
        self.assertNotIn(self.male.pk, results)

    def test_svekar_tast_stari_svat_filter_male(self):
        ids = self._field_ids("unos_vencanja")
        for name in ("svekar", "tast", "stari_svat"):
            results = self._ajax_ids(ids[name], term="Тест")
            self.assertIn(self.male.pk, results, msg=f"male missing from {name} lookup")
            self.assertNotIn(
                self.female.pk, results, msg=f"female leaked into {name} lookup"
            )

    def test_svekrva_tasta_filter_female(self):
        ids = self._field_ids("unos_vencanja")
        for name in ("svekrva", "tasta"):
            results = self._ajax_ids(ids[name], term="Тест")
            self.assertIn(
                self.female.pk, results, msg=f"female missing from {name} lookup"
            )
            self.assertNotIn(
                self.male.pk, results, msg=f"male leaked into {name} lookup"
            )

    def test_vencanje_kum_widget_has_no_gender_filter(self):
        ids = self._field_ids("unos_vencanja")
        results = self._ajax_ids(ids["kum"], term="Тест")
        for o in (self.male, self.female, self.legacy):
            self.assertIn(o.pk, results, msg=f"{o.ime} missing from kum lookup")

    def test_pol_none_passes_through_ajax(self):
        """A pol=None Osoba surfaces in BOTH male and female lookups."""
        ids = self._field_ids("unos_vencanja")
        male_results = self._ajax_ids(ids["zenik"], term="Тест")
        female_results = self._ajax_ids(ids["nevesta"], term="Тест")
        self.assertIn(self.legacy.pk, male_results)
        self.assertIn(self.legacy.pk, female_results)


# ---------------------------------------------------------------------------
# osoba_create.js carries the modal-toggle wiring
# ---------------------------------------------------------------------------


class OsobaCreateJsWiringTests(TestCase):
    """The shipped osoba_create.js must read data-osoba-default-pol and
    activate the matching toggle inside #modal-pol-toggle."""

    def test_osoba_create_reads_default_pol(self):
        import pathlib

        # Resolve relative to this test file so it works from any CWD.
        here = pathlib.Path(__file__).resolve().parent
        candidates = [
            here.parents[1] / "static" / "registar" / "components" / "osoba_create.js",
            here.parents[2]
            / "crkva"
            / "registar"
            / "static"
            / "registar"
            / "components"
            / "osoba_create.js",
        ]
        js_path = next((p for p in candidates if p.exists()), None)
        self.assertIsNotNone(
            js_path, msg=f"osoba_create.js not found at {candidates!r}"
        )
        js = js_path.read_text(encoding="utf-8")
        self.assertIn("data-osoba-default-pol", js)
        self.assertIn("modal-pol-toggle", js)
        # Sanity: the helper that flips the toggle must reference the
        # .tab-group__item class so it matches the modal markup.
        self.assertIn("tab-group__item", js)
