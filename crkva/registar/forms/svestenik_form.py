"""Django форма за унос свештеника."""

from django import forms
from registar.forms.select2 import ScriptAwareModelSelect2Widget
from registar.models import Parohija, Svestenik


class SvestenikForm(forms.ModelForm):
    """Формулар за унос новог свештеника."""

    class Meta:
        model = Svestenik
        fields = [
            "ime",
            "prezime",
            "zvanje",
            "mesto_rodjenja",
            "datum_rodjenja",
            "parohija",
        ]
        widgets = {
            "parohija": ScriptAwareModelSelect2Widget(
                model=Parohija,
                search_fields=["naziv__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "datum_rodjenja": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }
