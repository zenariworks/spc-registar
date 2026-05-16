"""Django форма за унос домаћинства."""

from django import forms
from django_select2.forms import ModelSelect2Widget
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
            "domacin": ModelSelect2Widget(
                model=Osoba,
                search_fields=["ime__icontains", "prezime__icontains"],
                attrs={"data-minimum-input-length": 2},
            ),
            "adresa": ModelSelect2Widget(
                model=Adresa,
                search_fields=["ulica__icontains", "mesto__icontains"],
                attrs={"data-minimum-input-length": 2},
            ),
            "slava": ModelSelect2Widget(
                model=Slava,
                search_fields=["naziv__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "napomena": forms.Textarea(attrs={"rows": 3}),
        }
