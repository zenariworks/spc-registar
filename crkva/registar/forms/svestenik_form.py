"""Django форма за унос свештеника."""

from django import forms
from registar.forms.distinct_lookup import DistinctValuesCharField
from registar.forms.select2 import ScriptAwareModelSelect2Widget
from registar.models import Adresa, Parohija, Svestenik


class SvestenikForm(forms.ModelForm):
    """Формулар за унос новог свештеника."""

    mesto_rodjenja = DistinctValuesCharField(
        required=False,
        label="место рођења",
        model_label="registar.Svestenik",
        source_fields=("mesto_rodjenja",),
    )

    class Meta:
        model = Svestenik
        fields = [
            "ime",
            "prezime",
            "zvanje",
            "mesto_rodjenja",
            "datum_rodjenja",
            "parohija",
            "adresa",
        ]
        widgets = {
            "parohija": ScriptAwareModelSelect2Widget(
                model=Parohija,
                search_fields=["naziv__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "adresa": ScriptAwareModelSelect2Widget(
                model=Adresa,
                search_fields=["ulica__icontains", "mesto__icontains"],
                attrs={
                    "data-minimum-input-length": 0,
                    "data-adresa-edit": "1",
                },
            ),
            "datum_rodjenja": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }
