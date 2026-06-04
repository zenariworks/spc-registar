"""Django форма за унос крштења."""

from django import forms
from registar.forms.distinct_lookup import DistinctValuesCharField
from registar.forms.select2 import (
    FemaleOsobaSelect2Widget,
    HramSelect2Widget,
    MaleOsobaSelect2Widget,
    OsobaSelect2Widget,
    ScriptAwareModelSelect2Widget,
    SvestenikSelect2Widget,
)
from registar.models import Krstenje




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
            "zivorodjeno",
            "po_redu",
            "vanbracno",
            "blizanac",
            "ime_blizanca",
            "telesna_mana",
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A kum is frequently from another parish — default the quick-add
        # “парохијан” toggle to off so they are not added to this roster.
        self.fields["kum"].widget.attrs["data-osoba-parohijan-default"] = "0"

    def clean(self):
        cleaned = super().clean()
        dete = cleaned.get("dete")
        otac = cleaned.get("otac")
        majka = cleaned.get("majka")
        kum = cleaned.get("kum")

        # Same Osoba cannot fill two roles.
        for role_a, name_a, role_b, name_b in (
            (dete, "dete", otac, "otac"),
            (dete, "dete", majka, "majka"),
            (dete, "dete", kum, "kum"),
            (otac, "otac", majka, "majka"),
            (otac, "otac", kum, "kum"),
            (majka, "majka", kum, "kum"),
        ):
            if role_a and role_b and role_a == role_b:
                self.add_error(name_b, f"Иста особа не може бити и {name_a} и {name_b}.")

        # If blizanac is checked, the second twin's name is required.
        if cleaned.get("blizanac") and not (cleaned.get("ime_blizanca") or "").strip():
            self.add_error("ime_blizanca",
                           "Унесите име другог детета близанца.")
        return cleaned
