"""Select2-style fields with on-the-fly creation of simple lookup rows.

Used for занимање / вероисповест / народност — single-field models where a
clerk legitimately wants to add a new value without leaving the form.
"""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django_select2.forms import ModelSelect2Widget


class TaggableLookupWidget(ModelSelect2Widget):
    """ModelSelect2Widget with select2 `tags: true` enabled so the user
    can pick an existing row OR create a new one from the typed text."""

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-tags", "true")
        attrs.setdefault("data-token-separators", "[]")
        # django-select2 sets this to 2 by default; force 1 so suggestions appear after one keystroke.
        attrs["data-minimum-input-length"] = 1
        attrs.setdefault("data-placeholder", "Изабери или унеси ново…")
        return attrs


class TaggableLookupField(forms.ModelChoiceField):
    """ModelChoiceField that creates a new row from a typed string
    when the submitted value isn't a numeric pk. The new row is
    populated via `get_or_create(**{create_field: value})`."""

    create_field = "naziv"

    def to_python(self, value):
        if value in self.empty_values:
            return None
        # First try as a pk (handles both integer and UUID primary keys).
        try:
            return self.queryset.get(pk=value)
        except (
            ValueError,
            TypeError,
            ValidationError,
            self.queryset.model.DoesNotExist,
        ):
            value = str(value).strip()
            if not value:
                return None
            obj, _ = self.queryset.model.objects.get_or_create(
                **{self.create_field: value}
            )
            return obj
