"""Django форма за унос парохијана."""

from django import forms
from registar.forms.distinct_lookup import DistinctValuesCharField
from registar.forms.lookup import (
    TaggableCreateMixin,
    TaggableLookupField,
    TaggableLookupWidget,
)
from registar.forms.phone import TenantPhoneField
from registar.forms.select2 import AdresaSelect2Widget
from registar.models import Narodnost, Osoba, Veroispovest, Zanimanje


class ParohijanForm(TaggableCreateMixin, forms.ModelForm):
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
    mesto_rodjenja = DistinctValuesCharField(
        required=False,
        label="место рођења",
        model_label="registar.Osoba",
        source_fields=("mesto_rodjenja",),
    )
    tel_mobilni = TenantPhoneField(label="Мобилни телефон", placeholder="061 234 5678")
    tel_fiksni = TenantPhoneField(label="Фиксни телефон", placeholder="011 234 5678")

    class Meta:
        model = Osoba
        fields = [
            "ime",
            "prezime",
            "devojacko_prezime",
            "gradjansko_ime",
            "mesto_rodjenja",
            "datum_rodjenja",
            "vreme_rodjenja",
            "pol",
            "zanimanje",
            "veroispovest",
            "narodnost",
            "adresa",
            "tel_mobilni",
            "tel_fiksni",
            "email",
        ]
        widgets = {
            "datum_rodjenja": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "vreme_rodjenja": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "pol": forms.RadioSelect,
            "adresa": AdresaSelect2Widget(),
        }
