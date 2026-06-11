"""Django форма за унос свештеника."""

from django import forms
from registar.forms.distinct_lookup import DistinctValuesCharField
from registar.forms.select2 import AdresaSelect2Widget, ParohijaSelect2Widget
from registar.models import Svestenik


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
            "parohija": ParohijaSelect2Widget(),
            "adresa": AdresaSelect2Widget(),
            "datum_rodjenja": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }
