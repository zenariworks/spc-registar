"""Shared select2 widget mixin that adds Cyrillic↔Latin search and
on-open suggestions to django-select2 dropdowns.
"""

from __future__ import annotations

import operator
from functools import reduce

from django.db.models import Q
from django_select2.forms import ModelSelect2Widget
from django_tenants.utils import schema_context
from registar.utils import get_query_variants


class ScriptAwareSelect2Mixin:
    """Mixin for `ModelSelect2Widget` subclasses that:

    1. Sets `data-minimum-input-length=0` so a click on the field shows
       suggestions even before the user types anything.
    2. Expands the search term via :func:`get_query_variants` so typing
       Latin matches Cyrillic data and vice versa.
    """

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-minimum-input-length"] = 0
        return attrs

    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        if queryset is None:
            queryset = self.get_queryset()
        search_fields = self.get_search_fields()

        if not search_fields or not term:
            return queryset

        variants = get_query_variants(term)
        if not variants:
            return queryset

        select = Q()
        for variant in variants:
            for bit in variant.split():
                or_queries = [Q(**{lookup: bit}) for lookup in search_fields]
                select |= reduce(operator.or_, or_queries)

        if dependent_fields:
            select &= Q(**dependent_fields)

        return queryset.filter(select).distinct()


class ScriptAwareModelSelect2Widget(ScriptAwareSelect2Mixin, ModelSelect2Widget):
    """Drop-in replacement for ModelSelect2Widget with Cyrillic↔Latin search."""


class PublicSchemaModelSelect2Widget(ScriptAwareModelSelect2Widget):
    """Select2 widget for shared (public-schema) models referenced by tenants.

    django-tenants switches the Postgres ``search_path`` per-request based on
    the request's tenant. Plain ``Model.objects.all()`` queries therefore look
    in the tenant schema. For models that physically live in the ``public``
    schema (e.g. :class:`kalendar.models.Slava`), that lookup fails because
    the table does not exist in the tenant schema.

    Every SQL access this widget performs — the cached widget config, the
    selected-option label render, and the AJAX search response — is wrapped
    in ``schema_context("public")`` so the queries always hit the public
    schema regardless of which tenant is currently active.
    """

    def set_to_cache(self):
        # Materialise queryset metadata while the public schema is active so
        # the cached ``queryset.query`` resolves the right table.
        with schema_context("public"):
            super().set_to_cache()

    def optgroups(self, name, value, attrs=None):
        # Rendering the selected <option> triggers a SELECT against Slava
        # via ``self.choices.queryset.filter(...)``. Run it in public schema.
        with schema_context("public"):
            return super().optgroups(name, value, attrs=attrs)

    def filter_queryset(self, request, term, queryset=None, **dependent_fields):
        with schema_context("public"):
            qs = super().filter_queryset(
                request, term, queryset=queryset, **dependent_fields
            )
            # Force evaluation while still inside the public schema context
            # so subsequent pagination/serialisation does not re-run the
            # query under the wrong search_path.
            return list(qs)


# ----------------------------------------------------------------------------
# Shared concrete widgets used by multiple forms. Living here avoids the
# 60-line copy-paste that previously sat at the top of krstenje_form.py and
# vencanje_form.py.
# ----------------------------------------------------------------------------

from django.db.models import Q  # noqa: E402

from registar.models import Adresa, Hram, Svestenik  # noqa: E402
from registar.models.parohijan import Osoba  # noqa: E402


class OsobaSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Osoba (unfiltered).

    Subclasses may set gender_filter to "М" or "Ж" to scope
    suggestions, and default_pol to seed the "+ Додај нову особу"
    modal that the JS layer opens from this widget.
    """

    model = Osoba
    search_fields = ["ime__icontains", "prezime__icontains"]
    gender_filter = None
    default_pol = None

    def get_queryset(self):
        qs = super().get_queryset()
        if self.gender_filter in ("М", "Ж"):
            # Lenient: include rows whose pol matches OR is NULL so legacy
            # uncategorised data still surfaces. pol__in=[value, None] does
            # NOT match NULL in SQL — OR an explicit isnull lookup instead.
            qs = qs.filter(Q(pol=self.gender_filter) | Q(pol__isnull=True))
        return qs

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-minimum-input-length"] = 0
        attrs["data-osoba-create"] = "1"
        if self.default_pol in ("М", "Ж"):
            attrs["data-osoba-default-pol"] = self.default_pol
        # Seeds the modal's парохијан toggle. Forms flip this to "0" for
        # roles usually not parishioners of this parish (kum / in-laws).
        attrs.setdefault("data-osoba-parohijan-default", "1")
        return attrs


class MaleOsobaSelect2Widget(OsobaSelect2Widget):
    """Osoba lookup restricted to pol=М (plus pol=NULL)."""

    gender_filter = "М"
    default_pol = "М"


class FemaleOsobaSelect2Widget(OsobaSelect2Widget):
    """Osoba lookup restricted to pol=Ж (plus pol=NULL)."""

    gender_filter = "Ж"
    default_pol = "Ж"


class SvestenikSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Svestenik."""

    model = Svestenik
    search_fields = ["ime__icontains", "prezime__icontains"]
    attrs = {"data-minimum-input-length": 0}


class HramSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Hram."""

    model = Hram
    search_fields = ["naziv__icontains"]
    attrs = {"data-minimum-input-length": 0}

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-create-modal"] = "hram-create-modal"
        attrs["data-create-label"] = "Додај нови храм"
        return attrs


class AdresaSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Adresa.

    Adds data-adresa-edit="1" via build_attrs so the inline-edit
    pencil component (registar/static/registar/components/adresa_edit.js)
    attaches its dropdown-row pencils to every dropdown opened from this
    widget. Class-level attrs={...} would not work: Django's
    Widget.__init__ overwrites self.attrs with {} when the widget is
    instantiated without an attrs argument (which is how Meta.widgets
    instantiates a widget class), so the only reliable place to inject
    default attrs is build_attrs.
    """

    model = Adresa
    search_fields = ["ulica__icontains", "mesto__icontains"]

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-adresa-edit"] = "1"
        attrs["data-create-modal"] = "adresa-create-modal"
        attrs["data-create-label"] = "Додај нову адресу"
        return attrs
