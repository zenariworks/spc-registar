"""Django форма за унос венчања."""

from django import forms
from django.db.models import Q
from registar.forms.select2 import ScriptAwareModelSelect2Widget
from registar.models import Hram, Svestenik, Vencanje
from registar.models.parohijan import Osoba


class OsobaSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Osoba model (unfiltered)."""

    model = Osoba
    search_fields = ["ime__icontains", "prezime__icontains"]
    #: When set to "М" or "Ж", restrict suggestions to that pol (plus
    #: ``pol=None`` so legacy uncategorised rows still surface). ``None``
    #: means no filter — any pol is allowed.
    gender_filter = None
    #: Default pol value to pre-select in the "+ Додај нову особу" modal
    #: when it is opened from this widget. ``None`` means no default.
    default_pol = None

    def get_queryset(self):
        qs = super().get_queryset()
        if self.gender_filter in ("М", "Ж"):
            # Lenient: include rows whose pol is the requested value OR
            # NULL (uncategorised legacy data). ``pol__in=[value, None]``
            # would NOT match NULL — the ORM compiles it to a plain IN
            # list, so we OR an explicit ``pol__isnull=True`` instead.
            qs = qs.filter(Q(pol=self.gender_filter) | Q(pol__isnull=True))
        return qs

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-minimum-input-length"] = 0
        attrs["data-osoba-create"] = "1"
        if self.default_pol in ("М", "Ж"):
            attrs["data-osoba-default-pol"] = self.default_pol
        return attrs


class MaleOsobaSelect2Widget(OsobaSelect2Widget):
    """Osoba lookup restricted to ``pol="М"`` (плюс ``pol=None``)."""

    gender_filter = "М"
    default_pol = "М"


class FemaleOsobaSelect2Widget(OsobaSelect2Widget):
    """Osoba lookup restricted to ``pol="Ж"`` (плюс ``pol=None``)."""

    gender_filter = "Ж"
    default_pol = "Ж"


class SvestenikSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Svestenik model."""

    model = Svestenik
    search_fields = ["ime__icontains", "prezime__icontains"]
    attrs = {"data-minimum-input-length": 0}


class HramSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Hram model."""

    model = Hram
    search_fields = ["naziv__icontains"]
    attrs = {"data-minimum-input-length": 0}


class VencanjeForm(forms.ModelForm):
    """Формулар за унос венчања."""

    class Meta:
        model = Vencanje
        fields = [
            # Редни број и година регистрације
            "redni_broj",
            "godina_registracije",
            # Регистар
            "knjiga",
            "strana",
            "broj",
            # Датум венчања
            "datum",
            # Особе (FK)
            "zenik",
            "nevesta",
            "kum",
            "svestenik",
            # Родитељи (нису у Osoba моделу)
            "svekar",
            "svekrva",
            "tast",
            "tasta",
            # Брак по реду
            "zenik_rb_brak",
            "nevesta_rb_brak",
            # Испитивање
            "datum_ispita",
            # Место венчања
            "hram",
            # Стари сват
            "stari_svat",
            # Разрешење и напомене
            "razresenje",
            "primedba",
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "datum_ispita": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "primedba": forms.Textarea(attrs={"rows": 3}),
            "zenik": MaleOsobaSelect2Widget,
            "nevesta": FemaleOsobaSelect2Widget,
            "kum": OsobaSelect2Widget,
            "svekar": MaleOsobaSelect2Widget,
            "svekrva": FemaleOsobaSelect2Widget,
            "tast": MaleOsobaSelect2Widget,
            "tasta": FemaleOsobaSelect2Widget,
            "stari_svat": MaleOsobaSelect2Widget,
            "svestenik": SvestenikSelect2Widget,
            "hram": HramSelect2Widget,
        }
