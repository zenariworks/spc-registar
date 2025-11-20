"""Django форма за унос парохијана."""

from django import forms
from django_select2.forms import ModelSelect2Widget
from registar.models import Parohijan, Zanimanje


class ParohijanForm(forms.ModelForm):
    """Формулар за унос и измену парохијана."""

    class Meta:
        model = Parohijan
        fields = [
            "ime",
            "prezime",
            "devojacko_prezime",
            "mesto_rodjenja",
            "datum_rodjenja",
            "vreme_rodjenja",
            "pol",
            "zanimanje",
            "veroispovest",
            "narodnost",
            "adresa",
        ]
        widgets = {
            "zanimanje": ModelSelect2Widget(
                model=Zanimanje,
                search_fields=["naziv__icontains"],
                attrs={"data-minimum-input-length": 3},
            ),
            "datum_rodjenja": forms.DateInput(attrs={"type": "date"}),
            "vreme_rodjenja": forms.TimeInput(attrs={"type": "time"}),
            "pol": forms.RadioSelect,
        }
