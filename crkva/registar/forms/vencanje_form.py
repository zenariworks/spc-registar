"""Django форма за унос венчања."""

from django import forms
from registar.forms.select2 import ScriptAwareModelSelect2Widget
from registar.models import Hram, Svestenik, Vencanje
from registar.models.parohijan import Osoba


class OsobaSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Osoba model."""

    model = Osoba
    search_fields = ["ime__icontains", "prezime__icontains"]

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["data-minimum-input-length"] = 0
        attrs["data-osoba-create"] = "1"
        return attrs


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
            "zenik": OsobaSelect2Widget,
            "nevesta": OsobaSelect2Widget,
            "kum": OsobaSelect2Widget,
            "svekar": OsobaSelect2Widget,
            "svekrva": OsobaSelect2Widget,
            "tast": OsobaSelect2Widget,
            "tasta": OsobaSelect2Widget,
            "stari_svat": OsobaSelect2Widget,
            "svestenik": SvestenikSelect2Widget,
            "hram": HramSelect2Widget,
        }
