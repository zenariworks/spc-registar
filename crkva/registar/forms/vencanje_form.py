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
            # Женик
            "ime_zenika",
            "prezime_zenika",
            "zanimanje_zenika",
            "mesto_zenika",
            "veroispovest_zenika",
            "narodnost_zenika",
            "adresa_zenika",
            # Невеста
            "ime_neveste",
            "prezime_neveste",
            "zanimanje_neveste",
            "mesto_neveste",
            "veroispovest_neveste",
            "narodnost_neveste",
            "adresa_neveste",
            # Родитељи
            "svekar",
            "svekrva",
            "tast",
            "tasta",
            # Рођење женика и невесте
            "datum_rodjenja_zenika",
            "mesto_rodjenja_zenika",
            "datum_rodjenja_neveste",
            "mesto_rodjenja_neveste",
            # Брак по реду
            "zenik_rb_brak",
            "nevesta_rb_brak",
            # Испитивање
            "datum_ispita",
            # Место венчања и свештеник
            "hram",
            "svestenik",
            # Кум и стари сват
            "kum",
            "stari_svat",
            # Разрешење и напомене
            "razresenje",
            "razresenje_primedba",
            "primedba",
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "datum_rodjenja_zenika": forms.DateInput(attrs={"type": "date"}),
            "datum_rodjenja_neveste": forms.DateInput(attrs={"type": "date"}),
            "datum_ispita": forms.DateInput(attrs={"type": "date"}),
            "razresenje_primedba": forms.Textarea(attrs={"rows": 3}),
            "primedba": forms.Textarea(attrs={"rows": 3}),
        }
