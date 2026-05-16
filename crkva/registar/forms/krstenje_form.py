"""Django форма за унос крштења."""

from django import forms
from django_select2.forms import ModelSelect2Widget
from registar.models import Hram, Krstenje, Svestenik
from registar.models.parohijan import Osoba


class OsobaSelect2Widget(ModelSelect2Widget):
    """Autocomplete widget for Osoba model."""

    model = Osoba
    search_fields = ["ime__icontains", "prezime__icontains"]
    attrs = {"data-minimum-input-length": 2}


class SvestenikSelect2Widget(ModelSelect2Widget):
    """Autocomplete widget for Svestenik model."""

    model = Svestenik
    search_fields = ["ime__icontains", "prezime__icontains"]
    attrs = {"data-minimum-input-length": 2}


class HramSelect2Widget(ModelSelect2Widget):
    """Autocomplete widget for Hram model."""

    model = Hram
    search_fields = ["naziv__icontains"]
    attrs = {"data-minimum-input-length": 2}


class KrstenjeForm(forms.ModelForm):
    """Формулар за унос крштења.

    Обухвата кључне податке из протокола, податке о детету, родитељима,
    месту/храму, куму и свештенику.
    """

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
            "datum": forms.DateInput(attrs={"type": "date"}),
            "vreme": forms.TimeInput(attrs={"type": "time"}),
            "datum_registracije": forms.DateInput(attrs={"type": "date"}),
            "primedba": forms.Textarea(attrs={"rows": 4}),
            "dete": OsobaSelect2Widget,
            "otac": OsobaSelect2Widget,
            "majka": OsobaSelect2Widget,
            "kum": OsobaSelect2Widget,
            "svestenik": SvestenikSelect2Widget,
            "hram": HramSelect2Widget,
        }
        help_texts = {
            "godina_registracije": "Година у којој је крштење забележено",
            "redni_broj": "Редни број крштења у текућој години",
        }
