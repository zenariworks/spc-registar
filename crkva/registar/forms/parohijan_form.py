from django import forms
from registar.models import Parohijan


class ParohijanForm(forms.ModelForm):
    class Meta:
        model = Parohijan
        fields = [
            "ime",
            "prezime",
            "mesto_rodjenja",
            "datum_rodjenja",
            "vreme_rodjenja",
            "pol",
            "devojacko_prezime",
            "zanimanje",
            "veroispovest",
            "narodnost",
            "adresa",
        ]
        widgets = {
            "datum_rodjenja": forms.DateInput(attrs={"type": "date"}),
            "vreme_rodjenja": forms.TimeInput(attrs={"type": "time"}),
        }
