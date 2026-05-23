"""Django форма за унос крштења."""

from django import forms
from registar.forms.distinct_lookup import DistinctValuesCharField
from django.db.models import Q
from registar.forms.select2 import (
    FemaleOsobaSelect2Widget,
    HramSelect2Widget,
    MaleOsobaSelect2Widget,
    OsobaSelect2Widget,
    ScriptAwareModelSelect2Widget,
    SvestenikSelect2Widget,
)
from registar.models import Hram, Krstenje, Svestenik
from registar.models.parohijan import Osoba




class HramSelect2Widget(ScriptAwareModelSelect2Widget):
    """Autocomplete widget for Hram model."""

    model = Hram
    search_fields = ["naziv__icontains"]
    attrs = {"data-minimum-input-length": 0}


class KrstenjeForm(forms.ModelForm):
    """Формулар за унос крштења.

    Обухвата кључне податке из протокола, податке о детету, родитељима,
    месту/храму, куму и свештенику.
    """

    mesto_registracije = DistinctValuesCharField(
        required=False,
        label="место регистрације",
        model_label="registar.Krstenje",
        source_fields=("mesto_registracije",),
    )

    class Meta:
        model = Krstenje
        fields = [
            # Протокол (регистар)
            "redni_broj",
            "godina_registracije",
            "knjiga",
            "broj",
            "strana",
            # Детаљи крштења
            "datum",
            "vreme",
            "hram",
            # Особе (FK)
            "dete",
            "otac",
            "majka",
            "kum",
            "svestenik",
            # Податци о детету
            "dete_rodjeno_zivo",
            "dete_po_redu_po_majci",
            "dete_vanbracno",
            "dete_blizanac",
            "drugo_dete_blizanac_ime",
            "dete_sa_telesnom_manom",
            # Матична књига – анаграф
            "mesto_registracije",
            "datum_registracije",
            "maticni_broj",
            "strana_registracije",
            # Напомена
            "primedba",
        ]
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "vreme": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "datum_registracije": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "primedba": forms.Textarea(attrs={"rows": 4}),
            "dete": OsobaSelect2Widget,
            "otac": MaleOsobaSelect2Widget,
            "majka": FemaleOsobaSelect2Widget,
            "kum": OsobaSelect2Widget,
            "svestenik": SvestenikSelect2Widget,
            "hram": HramSelect2Widget,
        }
        help_texts = {
            "godina_registracije": "Година у којој је крштење забележено",
            "redni_broj": "Редни број крштења у текућој години",
        }
