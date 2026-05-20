"""Django форма за унос домаћинства."""

from django import forms
from django.forms import inlineformset_factory
from registar.forms.phone import TenantPhoneField
from registar.forms.select2 import (
    PublicSchemaModelSelect2Widget,
    ScriptAwareModelSelect2Widget,
)
from registar.models import Adresa, Domacinstvo, Osoba, Slava, Ukucanin


class DomacinstvoForm(forms.ModelForm):
    """Формулар за унос новог домаћинства."""

    tel_mobilni = TenantPhoneField(label="Мобилни телефон", placeholder="061 234 5678")
    tel_fiksni = TenantPhoneField(label="Фиксни телефон", placeholder="011 234 5678")

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
                attrs={
                    "data-minimum-input-length": 0,
                    "data-adresa-edit": "1",
                },
            ),
            # Slava lives in the public schema (shared model); the dedicated
            # widget wraps every SQL call in schema_context("public") so the
            # select2 AJAX endpoint returns rows even inside a tenant request.
            "slava": PublicSchemaModelSelect2Widget(
                model=Slava,
                search_fields=["naziv__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "napomena": forms.Textarea(attrs={"rows": 3}),
        }


class UkucaninForm(forms.ModelForm):
    """Формулар за уређивање чланова домаћинства."""

    class Meta:
        model = Ukucanin
        fields = ["osoba", "ime_ukucana", "uloga", "preminuo"]
        widgets = {
            "osoba": ScriptAwareModelSelect2Widget(
                model=Osoba,
                search_fields=["ime__icontains", "prezime__icontains"],
                attrs={"data-minimum-input-length": 0},
            ),
            "ime_ukucana": forms.TextInput(
                attrs={"placeholder": "Име ако особа није у бази"}
            ),
        }


UkucaninFormSet = inlineformset_factory(
    Domacinstvo,
    Ukucanin,
    form=UkucaninForm,
    extra=1,
    can_delete=True,
)
