"""Django форма за унос крштења."""

from django import forms
from registar.forms.distinct_lookup import DistinctValuesCharField
from registar.forms.select2 import (
    FemaleOsobaSelect2Widget,
    HramSelect2Widget,
    MaleOsobaSelect2Widget,
    OsobaSelect2Widget,
    SvestenikSelect2Widget,
)
from registar.forms.validators import default_parohijan_off, validate_distinct_roles
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
        default_parohijan_off(self, ("kum",))
        # po_redu is 1-based ("по реду мајци"): floor the HTML input at 1
        # (server-side >=1 enforced by the model's MinValueValidator(1)).
        self.fields["po_redu"].widget.attrs["min"] = "1"

    def clean(self):
        cleaned = super().clean()
        # Same Osoba cannot fill two roles.
        validate_distinct_roles(self, ("dete", "otac", "majka", "kum"))

        # If blizanac is checked, the second twin's name is required.
        if cleaned.get("blizanac") and not (cleaned.get("ime_blizanca") or "").strip():
            self.add_error("ime_blizanca", "Унесите име другог детета близанца.")
        return cleaned
