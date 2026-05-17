"""Django форма за унос парохијана."""

from django import forms
from registar.forms.lookup import TaggableLookupField, TaggableLookupWidget
from registar.models import Narodnost, Parohijan, Veroispovest, Zanimanje


class ParohijanForm(forms.ModelForm):
    """Формулар за унос и измену парохијана."""

    zanimanje = TaggableLookupField(
        queryset=Zanimanje.objects.all(),
        required=False,
        label="Занимање",
        widget=TaggableLookupWidget(
            model=Zanimanje,
            search_fields=["naziv__icontains"],
        ),
    )
    veroispovest = TaggableLookupField(
        queryset=Veroispovest.objects.all(),
        required=False,
        label="Вероисповест",
        widget=TaggableLookupWidget(
            model=Veroispovest,
            search_fields=["naziv__icontains"],
        ),
    )
    narodnost = TaggableLookupField(
        queryset=Narodnost.objects.all(),
        required=False,
        label="Народност",
        widget=TaggableLookupWidget(
            model=Narodnost,
            search_fields=["naziv__icontains"],
        ),
    )

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
        ]
        widgets = {
            "datum_rodjenja": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "vreme_rodjenja": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "pol": forms.RadioSelect,
        }
