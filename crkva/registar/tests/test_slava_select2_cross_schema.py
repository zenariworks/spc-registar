"""Tests for the Slava select2 widget across the public/tenant schema boundary.

Slava lives in the public schema (shared model). The Domacinstvo form's
``slava`` widget is a :class:`PublicSchemaModelSelect2Widget` which wraps every
SQL call in ``schema_context("public")`` so the AJAX endpoint can return
results even inside a tenant request.

These tests assert:
- The Slava widget on DomacinstvoForm is the public-schema variant.
- ``filter_queryset`` returns the correct Slava rows when executed inside a
  tenant schema context (where the bare ``Slava.objects`` would otherwise fail
  because the table is not in the tenant schema).
- The select2 AJAX endpoint reachable at ``/select2/fields/auto.json`` resolves
  Slava rows when called from a tenant request.
"""

# pylint: disable=missing-function-docstring,missing-class-docstring

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.test.client import RequestFactory
from django_tenants.utils import schema_context
from kalendar.models import Slava
from registar.forms import DomacinstvoForm
from registar.forms.select2 import PublicSchemaModelSelect2Widget
from registar.models import Domacinstvo, Osoba
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()


class SlavaWidgetTypeTests(TestCase):
    def test_domacinstvo_form_slava_widget_is_public_schema_widget(self):
        form = DomacinstvoForm()
        widget = form.fields["slava"].widget
        self.assertIsInstance(widget, PublicSchemaModelSelect2Widget)
        self.assertEqual(widget.model, Slava)


class SlavaFilterQuerysetCrossSchemaTests(TestCase):
    """``filter_queryset`` must return Slava rows from the public schema even
    when invoked under the tenant search_path."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="slavasel", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        with schema_context("public"):
            cls.slava_jovan = Slava.objects.create(naziv="Свети Јован", dan=20, mesec=1)
            cls.slava_petar = Slava.objects.create(naziv="Свети Петар", dan=12, mesec=7)

    def test_filter_queryset_returns_public_slava_rows_inside_tenant(self):
        widget = DomacinstvoForm().fields["slava"].widget
        rf = RequestFactory()
        request = rf.get("/select2/fields/auto.json")
        # Simulate the AJAX call happening inside the tenant schema (where
        # bare Slava.objects.filter() would error because the `slave` table
        # is not in the tenant schema). The public-schema widget MUST still
        # return rows.
        results = widget.filter_queryset(request, "Јован", queryset=None)
        labels = [str(o) for o in results]
        self.assertTrue(
            any("Јован" in label for label in labels),
            f"expected Свети Јован in {labels!r}",
        )

    def test_filter_queryset_empty_term_returns_all_public_rows(self):
        widget = DomacinstvoForm().fields["slava"].widget
        rf = RequestFactory()
        results = widget.filter_queryset(rf.get("/"), "", queryset=None)
        # Two rows exist; widget MUST return them when no term is given.
        pks = {o.pk for o in results}
        self.assertIn(self.slava_jovan.pk, pks)
        self.assertIn(self.slava_petar.pk, pks)

    def test_get_queryset_does_not_break_set_to_cache(self):
        """``set_to_cache`` materialises ``queryset.query`` — the override must
        keep that path usable so widget caching still works."""
        widget = DomacinstvoForm().fields["slava"].widget
        # Render uses set_to_cache; build_attrs is needed first to assign uuid.
        widget.build_attrs({})
        # Should not raise (formerly broke when get_queryset returned a list).
        widget.set_to_cache()


class SlavaSelect2AjaxEndpointTests(TestCase):
    """End-to-end: the django_select2 AJAX endpoint must return Slava rows
    when called from inside a tenant request."""

    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="slavajson", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )
        cls.domacin = Osoba.objects.create(ime="Ђ", prezime="Тест", pol="М")
        cls.dom = Domacinstvo.objects.create(domacin=cls.domacin)
        with schema_context("public"):
            cls.slava = Slava.objects.create(naziv="Аранђеловдан", dan=21, mesec=11)

    def setUp(self):
        self.client = Client()

    def test_ajax_endpoint_returns_slava_for_tenant_user(self):
        self.client.force_login(self.clerk)
        # Render the edit form first so the widget is cached under a fresh uuid.
        from django.urls import reverse

        page = self.client.get(
            reverse("izmena_domacinstva", kwargs={"uid": self.dom.uid})
        )
        self.assertEqual(page.status_code, 200)
        body = page.content.decode("utf-8")
        # Extract the data-field_id for the slava widget so we can hit the
        # auto-json endpoint just as the browser would.
        idx = body.find('name="slava"')
        self.assertGreater(idx, -1)
        attr = 'data-field_id="'
        start = body.find(attr, idx)
        self.assertGreater(start, -1)
        start += len(attr)
        end = body.find('"', start)
        field_id = body[start:end]
        self.assertTrue(field_id)
        r = self.client.get(
            "/select2/fields/auto.json",
            {"field_id": field_id, "term": "Аранђ"},
        )
        self.assertEqual(r.status_code, 200, r.content)
        payload = r.json()
        labels = [row["text"] for row in payload.get("results", [])]
        self.assertTrue(
            any("Аранђеловдан" in lbl for lbl in labels),
            f"expected Аранђеловдан in {labels!r}",
        )
