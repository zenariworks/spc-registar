"""Select2-style widget for free-text fields that should suggest the
existing distinct values stored in that same column (or several columns
that share a domain — e.g. all `mesto_rodjenja` columns).

This is the Category-C analogue of TaggableLookupWidget: instead of
attaching to a separate lookup table, the autocomplete source is the
distinct values already entered in one or more CharField columns on
managed models.

Implementation strategy:

* We wrap a regular `forms.CharField` (the underlying model field is
  still `CharField`, NOT a FK).
* The widget renders as `<select>` with `data-tags="true"` so users may
  pick from the suggestions or type a brand-new value.
* For autocomplete we reuse django-select2's heavy-lifting infrastructure
  via `ModelSelect2Widget` but expose only a synthetic queryset of the
  distinct values. Each option's value is the literal string (not a pk)
  so the form roundtrips unchanged when posted.

Because django-select2 expects a `queryset` of model instances we use a
small adapter `_DistinctValueRow` that pretends to be one: it carries
just `pk` (== the string itself) and `__str__`. That keeps the rest of
the django-select2 plumbing happy without inventing a new Django field.
"""

from __future__ import annotations

from typing import Iterable

from django import forms
from django.apps import apps
from django.db.models import Q
from django_select2.forms import ModelSelect2Widget

from registar.utils import get_query_variants


class _DistinctValueRow:
    """Adapter that mimics a Django model instance for django-select2.

    We only need `pk` and `__str__` so the select2 endpoint can return
    JSON of {id, text} and the form can roundtrip the value.
    """

    def __init__(self, value: str):
        self.pk = value
        self.value = value

    def __str__(self) -> str:
        return self.value


class _DistinctValueQuerySet:
    """Iterable that quacks like a QuerySet of `_DistinctValueRow`s.

    django-select2's view calls `.filter()`, `.distinct()` and iterates.
    We back the whole thing with a plain SQL DISTINCT against the live
    column(s) so the suggestion list always reflects what's actually in
    the database for the current tenant.
    """

    def __init__(self, model_label: str, fields: tuple[str, ...]):
        self._model_label = model_label
        self._fields = fields
        self._term: str | None = None
        self._override_values = None

    def _model(self):
        app_label, model_name = self._model_label.split(".")
        return apps.get_model(app_label, model_name)

    def _values(self) -> list[str]:
        if self._override_values is not None:
            return list(self._override_values)
        model = self._model()
        collected: set[str] = set()
        for field in self._fields:
            qs = (
                model._default_manager.exclude(**{f"{field}__isnull": True})
                .exclude(**{field: ""})
                .values_list(field, flat=True)
                .distinct()
            )
            collected.update(qs)
        return sorted(collected)

    def filter(self, *args, **_kwargs):
        clone = _DistinctValueQuerySet(self._model_label, self._fields)
        for arg in args:
            if isinstance(arg, Q):
                clone._term = _extract_first_value(arg)
        return clone

    def distinct(self):
        return self

    def all(self):
        clone = _DistinctValueQuerySet(self._model_label, self._fields)
        clone._term = self._term
        clone._override_values = self._override_values
        return clone

    def none(self):
        clone = _DistinctValueQuerySet(self._model_label, self._fields)
        clone._override_values = []
        return clone

    def _materialised(self) -> list[_DistinctValueRow]:
        values = self._values()
        if self._term:
            term_lower = self._term.lower()
            values = [v for v in values if term_lower in v.lower()]
        return [_DistinctValueRow(v) for v in values]

    def __iter__(self):
        return iter(self._materialised())

    def __len__(self) -> int:
        return len(self._materialised())

    def __getitem__(self, item):
        return self._materialised()[item]

    def count(self) -> int:
        return self.__len__()

    def __bool__(self) -> bool:
        return True


def _extract_first_value(q: Q):
    """Return the first string value buried inside a Q tree."""
    for child in q.children:
        if isinstance(child, Q):
            found = _extract_first_value(child)
            if found:
                return found
        else:
            _key, value = child
            if value:
                return str(value)
    return None


class DistinctValuesSelect2Widget(ModelSelect2Widget):
    """Select2 widget for free-text CharField columns.

    Configure with `model_label="app.Model"` and `source_fields=("col",)`.
    Users get autocomplete suggestions sourced from the distinct values
    already present in those columns AND can type a brand-new value
    (because `data-tags=true`).
    """

    model_label: str = ""
    source_fields: tuple[str, ...] = ()

    def __init__(self, *args, model_label: str | None = None,
                 source_fields: Iterable[str] | None = None, **kwargs):
        if model_label is not None:
            self.model_label = model_label
        if source_fields is not None:
            self.source_fields = tuple(source_fields)
        kwargs.setdefault("queryset", _DistinctValueQuerySet(
            self.model_label, self.source_fields
        ))
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return _DistinctValueQuerySet(self.model_label, self.source_fields)

    def get_search_fields(self):
        # Required by ModelSelect2Widget. Actual filtering is handled in
        # filter_queryset below; this list just satisfies the parent.
        return ["pk__icontains"]

    def set_to_cache(self):
        """Override the parent's pickling-based caching.

        ModelSelect2Widget caches `[queryset.none(), queryset.query]` so
        the AJAX view can rebuild a real QuerySet. Our synthetic queryset
        has no SQL `.query` to serialise, so we instead stash the params
        needed to rebuild the synthetic queryset on the receiving end
        (the AJAX view unpacks the 2-tuple into `qs, qs.query` and then
        calls `qs.all()` to get the queryset it will pass to
        `filter_queryset`).
        """
        from django.core.cache import cache as django_cache

        synthetic = _DistinctValueQuerySet(self.model_label, self.source_fields)
        synthetic.query = None  # unpacked by AJAX view; we don't use it
        django_cache.set(
            self._get_cache_key(),
            {
                "queryset": (synthetic, None),
                "cls": self.__class__,
                "search_fields": tuple(self.search_fields),
                "max_results": int(self.max_results),
                "url": str(self.get_url()),
                "dependent_fields": dict(self.dependent_fields),
                # widget_cls(**widget_dict) needs to accept these kwargs.
                "model_label": self.model_label,
                "source_fields": tuple(self.source_fields),
            },
        )

    def filter_queryset(self, request, term, queryset=None, **_dependent_fields):
        qs = _DistinctValueQuerySet(self.model_label, self.source_fields)
        if not term:
            return qs
        variants = get_query_variants(term) or [term]
        all_values = qs._values()
        matched: list[str] = []
        seen: set[str] = set()
        for variant in variants:
            v_lower = variant.lower()
            for value in all_values:
                if value in seen:
                    continue
                if v_lower in value.lower():
                    matched.append(value)
                    seen.add(value)
        clone = _DistinctValueQuerySet(self.model_label, self.source_fields)
        clone._override_values = matched
        return clone

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-tags", "true")
        attrs.setdefault("data-token-separators", "[]")
        attrs["data-minimum-input-length"] = 0
        attrs.setdefault("data-placeholder", "Изабери или унеси ново…")
        return attrs

    def optgroups(self, name, value, attrs=None):
        """Render the currently-selected value as a pre-selected <option>.

        For a tags-style widget we want the existing value (if any) to
        show up as the selected option so the user sees what was saved
        instead of an empty pill.
        """
        groups = []
        if value:
            for val in value:
                if not val:
                    continue
                groups.append((
                    None,
                    [{
                        "name": name,
                        "value": val,
                        "label": val,
                        "selected": True,
                        "index": "0",
                        "attrs": {"selected": True},
                        "type": "select",
                        "template_name": "django/forms/widgets/select_option.html",
                        "wrap_label": True,
                    }],
                    0,
                ))
        return groups


class DistinctValuesCharField(forms.CharField):
    """CharField backed by `DistinctValuesSelect2Widget`.

    Use on ModelForms in place of the default CharField so the form
    submits the raw typed/picked string to the underlying CharField on
    the model.
    """

    def __init__(self, *args, model_label: str, source_fields: Iterable[str],
                 **kwargs):
        widget = kwargs.pop(
            "widget",
            DistinctValuesSelect2Widget(
                model_label=model_label,
                source_fields=tuple(source_fields),
            ),
        )
        super().__init__(*args, widget=widget, **kwargs)
