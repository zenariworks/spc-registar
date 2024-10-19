from django import forms
from registar.models import Krstenje


class KrstenjeForm(forms.ModelForm):
    class Meta:
        model = Krstenje
        fields = [
            "knjiga",
            "broj",
            "strana",
            "datum",
            "vreme",
            "hram",
            "mesto",
            "svestenik",
        ]
        labels = {
            "knjiga": "Протоколарна књига",
            "broj": "Текући број",
            "strana": "Протоколарна страна",
            "datum": "Датум крштења",
            "vreme": "Време крштења",
            "hram": "Место крштења",
            "mana": "Мана",
            "svestenik": "Свештеник",
        }
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "vreme": forms.TimeInput(attrs={"type": "time"}),
        }
