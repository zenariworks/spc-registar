"""Django форма за унос крштења."""

from django import forms
from registar.models import Krstenje


class KrstenjeForm(forms.ModelForm):
    """Формулар за унос крштења.

    Обухвата кључне податке из протокола, податке о детету, родитељима,
    месту/храму, куму и свештенику.
    """

    class Meta:
        model = Krstenje
        fields = [
            # Протокол (регистар)
            "redni_broj_krstenja_tekuca_godina",
            "krstenje_tekuca_godina",
            "knjiga",
            "broj",
            "strana",

            # Детаљи крштења
            "datum",
            "vreme",
            "mesto",
            "hram",

            # Дете
            "adresa_deteta_grad",
            "adresa_deteta_ulica",
            "adresa_deteta_broj",
            "datum_rodjenja",
            "vreme_rodjenja",
            "mesto_rodjenja",
            "ime_deteta",
            "gradjansko_ime_deteta",
            "pol_deteta",

            # Родитељи
            "ime_oca",
            "prezime_oca",
            "zanimanje_oca",
            "adresa_oca_mesto",
            "veroispovest_oca",
            "narodnost_oca",
            "ime_majke",
            "prezime_majke",
            "zanimanje_majke",
            "adresa_majke_mesto",
            "veroispovest_majke",

            # Податци о детету
            "dete_rodjeno_zivo",
            "dete_po_redu_po_majci",
            "dete_vanbracno",
            "dete_blizanac",
            "drugo_dete_blizanac_ime",
            "dete_sa_telesnom_manom",

            # Свештеник и Кум
            "svestenik",
            "ime_kuma",
            "prezime_kuma",
            "zanimanje_kuma",
            "adresa_kuma_mesto",

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
            "datum_rodjenja": forms.DateInput(attrs={"type": "date"}),
            "vreme_rodjenja": forms.TimeInput(attrs={"type": "time"}),
            "datum_registracije": forms.DateInput(attrs={"type": "date"}),
            "primedba": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "krstenje_tekuca_godina": "Година у којој је крштење забележено",
            "redni_broj_krstenja_tekuca_godina": "Редни број крштења у текућој години",
        }
