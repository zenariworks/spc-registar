"""Shared select2 widget mixin that adds Cyrillic↔Latin search and
on-open suggestions to django-select2 dropdowns.
"""

from __future__ import annotations

import operator
from functools import reduce

from django.db.models import Q
from django_select2.forms import ModelSelect2Widget
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
