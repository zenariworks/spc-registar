from django import forms
from registar.models import Krstenje


class KrstenjeForm(forms.ModelForm):
    class Meta:
        model = Krstenje
        fields = [
            "knjiga_krstenja",
            "broj_krstenja",
            "strana_krstenja",
            "datum_krstenja",
            "vreme_krstenja",
            "hram",
            "svestenik",
        ]
        labels = {
            "knjiga_krstenja": "Протоколарна књига",
            "broj_krstenja": "Текући број",
            "strana_krstenja": "Протоколарна страна",
            "datum_krstenja": "Датум крштења",
            "vreme_krstenja": "Време крштења",
            "hram": "Место крштења",
            "mana": "Мана",
            "svestenik": "Свештеник",
        }
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "vreme": forms.TimeInput(attrs={"type": "time"}),
        }
