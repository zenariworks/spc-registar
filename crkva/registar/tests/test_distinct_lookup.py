"""Tests for the DistinctValues typed-lookup widget (Category C).

For each free-text CharField that was converted to a typed lookup, we
verify that:

1. The widget is the DistinctValuesSelect2Widget (so it renders as
   <select class="django-select2" data-tags="true">).
2. Posting the form with an existing string value saves correctly.
3. Posting the form with a brand-new string value also saves
   (the widget allows free text — it doesn't reject novel values).
4. The django-select2 AJAX endpoint returns the existing distinct
   values as suggestions when queried.
"""

# pylint: disable=missing-function-docstring

import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.forms.distinct_lookup import DistinctValuesSelect2Widget
from registar.models import Krstenje, Osoba, Svestenik
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


# ---------------------------------------------------------------------------
# Widget unit tests
# ---------------------------------------------------------------------------


class DistinctValuesWidgetTests(TestCase):
    """The widget surfaces existing distinct values for autocomplete."""

    @classmethod
    def setUpTestData(cls):
        Osoba.objects.create(ime="А", prezime="Један", mesto_rodjenja="Београд")
        Osoba.objects.create(ime="Б", prezime="Два", mesto_rodjenja="Нови Сад")
        Osoba.objects.create(ime="В", prezime="Три", mesto_rodjenja="Београд")
        Osoba.objects.create(ime="Г", prezime="Без", mesto_rodjenja=None)
        Osoba.objects.create(ime="Д", prezime="Празно", mesto_rodjenja="")

    def test_widget_lists_distinct_existing_values(self):
        widget = DistinctValuesSelect2Widget(
            model_label="registar.Osoba",
            source_fields=("mesto_rodjenja",),
        )
        qs = widget.filter_queryset(request=None, term="")
        values = [row.value for row in qs]
        self.assertIn("Београд", values)
        self.assertIn("Нови Сад", values)
        self.assertEqual(values.count("Београд"), 1, "distinct: Београд once")

    def test_widget_search_filters_to_matching_values(self):
        widget = DistinctValuesSelect2Widget(
            model_label="registar.Osoba",
            source_fields=("mesto_rodjenja",),
        )
        qs = widget.filter_queryset(request=None, term="Београд")
        values = [row.value for row in qs]
        self.assertEqual(values, ["Београд"])

    def test_widget_search_latin_matches_cyrillic(self):
        widget = DistinctValuesSelect2Widget(
            model_label="registar.Osoba",
            source_fields=("mesto_rodjenja",),
        )
        qs = widget.filter_queryset(request=None, term="Beograd")
        values = [row.value for row in qs]
        self.assertIn("Београд", values)

    def test_widget_excludes_null_and_empty_values(self):
        widget = DistinctValuesSelect2Widget(
            model_label="registar.Osoba",
            source_fields=("mesto_rodjenja",),
        )
        qs = widget.filter_queryset(request=None, term="")
        values = [row.value for row in qs]
        self.assertNotIn("", values)
        self.assertNotIn(None, values)

    def test_widget_renders_with_tags_enabled(self):
        widget = DistinctValuesSelect2Widget(
            model_label="registar.Osoba",
            source_fields=("mesto_rodjenja",),
        )
        attrs = widget.build_attrs({})
        self.assertEqual(attrs.get("data-tags"), "true")
        self.assertEqual(attrs.get("data-minimum-input-length"), 0)


# ---------------------------------------------------------------------------
# Posting through the form
# ---------------------------------------------------------------------------


class _ClerkLoggedInMixin:
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(
            username=f"distinct-clerk-{cls.__name__.lower()}", password="x"
        )
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)


class ParohijanMestoRodjenjaPostTests(_ClerkLoggedInMixin, TestCase):
    """`mesto_rodjenja` accepts a typed string and saves it verbatim."""

    def test_posting_existing_value_roundtrips(self):
        Osoba.objects.create(ime="Пред", prezime="Постоји", mesto_rodjenja="Ниш")
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Нови",
                "prezime": "Парохијан",
                "pol": "М",
                "mesto_rodjenja": "Ниш",
            },
        )
        self.assertEqual(r.status_code, 302)
        p = Osoba.objects.get(ime="Нови", prezime="Парохијан")
        self.assertEqual(p.mesto_rodjenja, "Ниш")

    def test_posting_new_value_saves_verbatim(self):
        r = self.client.post(
            reverse("unos_parohijana"),
            {
                "ime": "Бранд",
                "prezime": "Нови",
                "pol": "М",
                "mesto_rodjenja": "Краљево",
            },
        )
        self.assertEqual(r.status_code, 302)
        p = Osoba.objects.get(ime="Бранд")
        self.assertEqual(p.mesto_rodjenja, "Краљево")


class SvestenikMestoRodjenjaFormTests(TestCase):
    """Svestenik form's `mesto_rodjenja` uses the typed-lookup widget."""

    def test_form_field_is_distinct_values_widget(self):
        from registar.forms import SvestenikForm

        form = SvestenikForm()
        widget = form.fields["mesto_rodjenja"].widget
        self.assertIsInstance(widget, DistinctValuesSelect2Widget)
        rendered = str(form["mesto_rodjenja"])
        self.assertIn('class="django-select2', rendered)
        self.assertIn('data-tags="true"', rendered)

    def test_post_saves_mesto_rodjenja(self):
        admin = User.objects.create_superuser(
            username="svest-mr", email="m@x.test", password="x"
        )
        client = Client()
        client.force_login(admin)
        r = client.post(
            reverse("unos_svestenika"),
            {
                "ime": "Свешт",
                "prezime": "МестоТест",
                "zvanje": "јереј",
                "mesto_rodjenja": "Крагујевац",
            },
        )
        self.assertEqual(r.status_code, 302)
        s = Svestenik.objects.get(ime="Свешт", prezime="МестоТест")
        self.assertEqual(s.mesto_rodjenja, "Крагујевац")


class KrstenjeMestoRegistracijeFormTests(TestCase):
    """Krstenje form's `mesto_registracije` uses the typed-lookup widget."""

    def test_form_field_is_distinct_values_widget(self):
        from registar.forms import KrstenjeForm

        form = KrstenjeForm()
        widget = form.fields["mesto_registracije"].widget
        self.assertIsInstance(widget, DistinctValuesSelect2Widget)
        rendered = str(form["mesto_registracije"])
        self.assertIn('class="django-select2', rendered)


# ---------------------------------------------------------------------------
# AJAX endpoint exercises the widget
# ---------------------------------------------------------------------------


class AutoJsonEndpointTests(TestCase):
    """The /select2/fields/auto.json endpoint returns existing distinct
    values for fields rendered via DistinctValuesSelect2Widget.
    """

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.user = User.objects.create_user(username="auto-json-tester", password="x")
        UserMembership.objects.create(
            user=cls.user, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        Osoba.objects.create(ime="Тест", prezime="Један", mesto_rodjenja="Београд")
        Osoba.objects.create(ime="Тест", prezime="Два", mesto_rodjenja="Нови Сад")

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_auto_json_returns_existing_values_for_mesto_rodjenja(self):
        # First load the form to obtain the field_id (django-select2 stores
        # widget state server-side keyed by an opaque token in the rendered
        # <select>'s data-field_id attribute).
        r = self.client.get(reverse("unos_parohijana"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        import re

        match = re.search(
            r'<select[^>]*name="mesto_rodjenja"[^>]*data-field_id="([^"]+)"',
            html,
        )
        self.assertIsNotNone(match, "mesto_rodjenja <select> must carry data-field_id")
        field_id = match.group(1)

        # Hit the auto.json endpoint with an empty term — every distinct
        # value should come back.
        ajax = self.client.get(
            "/select2/fields/auto.json",
            {"field_id": field_id, "term": "", "_type": "query"},
        )
        self.assertEqual(ajax.status_code, 200)
        data = ajax.json()
        texts = [row["text"] for row in data.get("results", [])]
        self.assertIn("Београд", texts)
        self.assertIn("Нови Сад", texts)

    def test_auto_json_filters_by_search_term(self):
        r = self.client.get(reverse("unos_parohijana"))
        html = r.content.decode()
        import re

        match = re.search(
            r'<select[^>]*name="mesto_rodjenja"[^>]*data-field_id="([^"]+)"',
            html,
        )
        field_id = match.group(1)
        ajax = self.client.get(
            "/select2/fields/auto.json",
            {"field_id": field_id, "term": "Београд", "_type": "query"},
        )
        self.assertEqual(ajax.status_code, 200)
        data = ajax.json()
        texts = [row["text"] for row in data.get("results", [])]
        self.assertIn("Београд", texts)
        self.assertNotIn("Нови Сад", texts)


class KrstenjeAutoJsonEndpointTests(TestCase):
    """The auto.json endpoint also returns mesto_registracije suggestions."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="krst-auto-json", email="kj@x.test", password="x"
        )
        Krstenje.objects.create(
            godina_registracije=2024,
            redni_broj=1,
            knjiga=1,
            strana=1,
            broj=1,
            datum=datetime.date(2024, 1, 1),
            dete_rodjeno_zivo=True,
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
            mesto_registracije="Земун",
        )
        Krstenje.objects.create(
            godina_registracije=2024,
            redni_broj=2,
            knjiga=1,
            strana=2,
            broj=2,
            datum=datetime.date(2024, 2, 1),
            dete_rodjeno_zivo=True,
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
            mesto_registracije="Чачак",
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_auto_json_returns_krstenje_mesto_registracije(self):
        r = self.client.get(reverse("unos_krstenja"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        import re

        match = re.search(
            r'<select[^>]*name="mesto_registracije"[^>]*data-field_id="([^"]+)"',
            html,
        )
        self.assertIsNotNone(
            match,
            "mesto_registracije <select> must carry data-field_id (= typed-lookup is wired)",
        )
        field_id = match.group(1)
        ajax = self.client.get(
            "/select2/fields/auto.json",
            {"field_id": field_id, "term": "", "_type": "query"},
        )
        self.assertEqual(ajax.status_code, 200)
        texts = [row["text"] for row in ajax.json().get("results", [])]
        self.assertIn("Земун", texts)
        self.assertIn("Чачак", texts)
