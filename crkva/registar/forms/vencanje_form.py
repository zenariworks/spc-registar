"""Django форма за унос венчања."""

from django import forms
from registar.forms.select2 import (
    FemaleOsobaSelect2Widget,
    HramSelect2Widget,
    MaleOsobaSelect2Widget,
    OsobaSelect2Widget,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Witnesses and in-laws are frequently not parishioners of this parish;
        # default their quick-add “парохијан” toggle to off. The couple
        # (женик/невеста) keep the on default.
        for _f in ("kum", "svekar", "svekrva", "tast", "tasta", "stari_svat"):
            self.fields[_f].widget.attrs["data-osoba-parohijan-default"] = "0"

    def clean(self):
        cleaned = super().clean()
        roles = [
            ("zenik", cleaned.get("zenik")),
            ("nevesta", cleaned.get("nevesta")),
            ("kum", cleaned.get("kum")),
            ("svekar", cleaned.get("svekar")),
            ("svekrva", cleaned.get("svekrva")),
            ("tast", cleaned.get("tast")),
            ("tasta", cleaned.get("tasta")),
            ("stari_svat", cleaned.get("stari_svat")),
        ]
        # Pairwise: same Osoba cannot fill two roles in the same vencanje.
        for i, (name_a, val_a) in enumerate(roles):
            if not val_a:
                continue
            for name_b, val_b in roles[i + 1 :]:
                if val_b and val_a == val_b:
                    self.add_error(
                        name_b, f"Иста особа не може бити и {name_a} и {name_b}."
                    )
        return cleaned
