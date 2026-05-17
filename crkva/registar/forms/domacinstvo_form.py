"""Django форма за унос домаћинства."""

from django import forms
from registar.forms.select2 import ScriptAwareModelSelect2Widget
from registar.models import Adresa, Domacinstvo, Osoba, Slava


class DomacinstvoForm(forms.ModelForm):
    """Формулар за унос новог домаћинства."""

    class Meta:
        model = Domacinstvo
        fields = [
            "domacin",
            "adresa",
            "slava",
            "tel_fiksni",
            "tel_mobilni",
            "slavska_vodica",
            "vaskrsnja_vodica",
            "napomena",
        ]
        widgets = {
            "domacin": ScriptAwareModelSelect2Widget(
                model=Osoba,
                search_fields=["ime__icontains", "prezime__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "adresa": ScriptAwareModelSelect2Widget(
                model=Adresa,
                search_fields=["ulica__icontains", "mesto__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "slava": ScriptAwareModelSelect2Widget(
                model=Slava,
                search_fields=["naziv__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "napomena": forms.Textarea(attrs={"rows": 3}),
        }
