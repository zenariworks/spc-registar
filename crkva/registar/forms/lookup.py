"""Select2-style fields with deferred creation of simple lookup rows.

Used for занимање / вероисповест / народност — single-field models where a
clerk legitimately wants to add a new value without leaving the form.

Нова вредност се НЕ прави у ``to_python`` (то би оставило ред-сироче ако
друго поље падне на валидацији, а ``MultipleObjectsReturned`` би срушио
страницу). ``to_python`` враћа ``PendingLookup`` маркер, а
``TaggableCreateMixin.save`` га материјализује тек пошто цела форма прође
валидацију (issue #252).
"""

from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django_select2.forms import ModelSelect2Widget
from registar.text_utils import normalize_naziv


class PendingLookup:
    """Маркер за нову (откуцану) lookup вредност која још није креирана."""

    __slots__ = ("label",)

    def __init__(self, label: str):
        self.label = label

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"PendingLookup({self.label!r})"

    def __eq__(self, other) -> bool:
        return isinstance(other, PendingLookup) and other.label == self.label

    def __hash__(self) -> int:
        return hash(self.label)


def get_or_create_lookup(model, label: str, field: str = "naziv"):
    """Врати постојећи lookup ред (case-insensitive) или направи нови.

    Користи ``filter().first()`` уместо ``get_or_create`` да истоимени
    дупликати не подигну ``MultipleObjectsReturned``; нормализује назив пре
    поређења/уписа (#252).
    """
    label = normalize_naziv(label)
    obj = model.objects.filter(**{f"{field}__iexact": label}).first()
    if obj is None:
        obj = model.objects.create(**{field: label})
    return obj


class TaggableLookupWidget(ModelSelect2Widget):
    """ModelSelect2Widget with select2 ``tags: true`` enabled so the user
    can pick an existing row OR type a new one."""

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-tags", "true")
        attrs.setdefault("data-token-separators", "[]")
        # django-select2 default is 2; force 0 so suggestions appear at once.
        attrs["data-minimum-input-length"] = 0
        attrs.setdefault("data-placeholder", "Изабери или унеси ново…")
        return attrs

    def _looks_like_pk(self, value):
        """Да ли вредност може бити PK модела (а не откуцани нови назив)."""
        if value in self.choices.field.empty_values:
            return False
        pk_field = self.choices.queryset.model._meta.pk
        try:
            pk_field.to_python(value)
            return True
        except (ValueError, TypeError, ValidationError):
            return False

    def optgroups(self, name, value, attrs=None):
        # Tags режим: вредност може бити свеже откуцани назив (није PK).
        # Прослеђивање таквог назива базном optgroups позива
        # queryset.filter(pk__in=[назив]) и пуца при кастовању у тип PK
        # (нпр. UUID) — нпр. при поновном приказу неисправне форме. Зато
        # такве називе исцртавамо као литералне изабране опције, а базној
        # класи дајемо само стварне PK-ове (#252).
        pk_values = [v for v in value if self._looks_like_pk(v)]
        literal = [
            v
            for v in value
            if v not in self.choices.field.empty_values and v not in pk_values
        ]
        groups = super().optgroups(name, pk_values, attrs=attrs)
        default = groups[0][1]
        for label in literal:
            default.append(self.create_option(name, label, label, True, len(default)))
        return groups


class TaggableLookupField(forms.ModelChoiceField):
    """Resolve an existing row by pk. A typed-in new value is returned as a
    :class:`PendingLookup` marker (NOT created here) so it is materialised
    only after the whole form validates — see :class:`TaggableCreateMixin`
    (issue #252)."""

    def to_python(self, value):
        if value in self.empty_values:
            return None
        # Existing row chosen from the dropdown → value is the pk.
        try:
            return self.queryset.get(pk=value)
        except (
            ValueError,
            TypeError,
            ValidationError,
            self.queryset.model.DoesNotExist,
        ):
            label = normalize_naziv(str(value))
            if not label:
                return None
            return PendingLookup(label)

    def validate(self, value):
        # New values are pending creation; skip ModelChoiceField's
        # "valid choice" queryset check. These fields are optional, so a
        # missing value is fine and a PendingLookup is a deliberate entry.
        if isinstance(value, PendingLookup):
            return
        super().validate(value)


class TaggableCreateMixin:
    """ModelForm mixin that materialises :class:`PendingLookup` values in
    ``save()``.

    Creation happens only after the whole form validates (``save`` runs solely
    on valid forms), so a failed sibling field can no longer orphan a lookup
    row (issue #252). During ``_post_clean`` the markers are stripped to
    ``None`` so ``construct_instance`` does not assign a non-model value to a
    FK; ``save`` then resolves/creates the real rows and sets them.
    """

    def _taggable_field_names(self):
        return [
            name
            for name, field in self.fields.items()
            if isinstance(field, TaggableLookupField)
        ]

    def _post_clean(self):
        self._pending_lookups = {}
        for name in self._taggable_field_names():
            value = self.cleaned_data.get(name)
            if isinstance(value, PendingLookup):
                self._pending_lookups[name] = value.label
                self.cleaned_data[name] = None
        super()._post_clean()

    def save(self, commit=True):
        for name, label in getattr(self, "_pending_lookups", {}).items():
            model = self.fields[name].queryset.model
            setattr(self.instance, name, get_or_create_lookup(model, label))
        return super().save(commit=commit)
