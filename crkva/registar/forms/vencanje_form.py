"""Django форма за унос венчања."""

from django import forms
from registar.models import Vencanje


class VencanjeForm(forms.ModelForm):
    """Формулар за унос венчања."""

    class Meta:
        model = Vencanje
        fields = [
            # Текућа година и редни број
            "redni_broj_vencanja_tekuca_godina",
            "vencanje_tekuca_godina",
            # Регистар
            "knjiga",
            "strana",
            "tekuci_broj",
            # Датум венчања
            "datum",
            # Особе (FK)
            "zenik",
            "nevesta",
            "kum",
            "svestenik",
            # Адресе (специфичне за догађај)
            "mesto_zenika",
            "adresa_zenika",
            "mesto_neveste",
            "adresa_neveste",
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
            "razresenje_primedba",
            "primedba",
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "datum_ispita": forms.DateInput(attrs={"type": "date"}),
            "razresenje_primedba": forms.Textarea(attrs={"rows": 3}),
            "primedba": forms.Textarea(attrs={"rows": 3}),
        }
