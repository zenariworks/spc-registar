"""Django форма за унос венчања."""

from django import forms
from registar.forms.select2 import (
    FemaleOsobaSelect2Widget,
    HramSelect2Widget,
    MaleOsobaSelect2Widget,
    OsobaSelect2Widget,
    ScriptAwareModelSelect2Widget,
    SvestenikSelect2Widget,
)
from registar.models import Vencanje




class VencanjeForm(forms.ModelForm):
    """Формулар за унос венчања."""

    class Meta:
        model = Vencanje
        fields = [
            # Редни број и година регистрације
            "redni_broj",
            "godina_registracije",
            # Регистар
            "knjiga",
            "strana",
            "broj",
            # Датум венчања
            "datum",
            # Особе (FK)
            "zenik",
            "nevesta",
            "kum",
            "svestenik",
            # Родитељи (нису у Osoba моделу)
            "svekar",
            "svekrva",
            "tast",
            "tasta",
            # Брак по реду
            "zenik_rb_brak",
            "nevesta_rb_brak",
            # Испитивање
            "datum_ispita",
            # Место венчања
            "hram",
            # Стари сват
            "stari_svat",
            # Разрешење и напомене
            "razresenje",
            "primedba",
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "datum_ispita": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "primedba": forms.Textarea(attrs={"rows": 3}),
            "zenik": MaleOsobaSelect2Widget,
            "nevesta": FemaleOsobaSelect2Widget,
            "kum": OsobaSelect2Widget,
            "svekar": MaleOsobaSelect2Widget,
            "svekrva": FemaleOsobaSelect2Widget,
            "tast": MaleOsobaSelect2Widget,
            "tasta": FemaleOsobaSelect2Widget,
            "stari_svat": MaleOsobaSelect2Widget,
            "svestenik": SvestenikSelect2Widget,
            "hram": HramSelect2Widget,
        }
