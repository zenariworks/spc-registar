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
            "dete",
            "dete_majci",
            "dete_bracno",
            "mana",
            "blizanac",
            "otac",
            "majka",
            "svestenik",
            "kum",
            "primedba",
        ]
        labels = {
            "knjiga_krstenja": "Протоколарна књига",
            "broj_krstenja": "Текући број",
            "strana_krstenja": "Протоколарна страна",
            "datum_krstenja": "Датум крштења",
            "vreme_krstenja": "Време крштења",
            
            "hram": "Место крштења",
            "dete": "Дете",
            "dete_majci": "Дете по реду (по мајци)",
            "dete_bracno": "Брачно дете",
            "mana": "Мана",
            "blizanac": "Близанац",
            "otac": "Отац",
            "majka": "Мајка",
            "svestenik": "Свештеник",
            "kum": "Кум",
            "primedba": "Примедба",
        }
        widgets = {
            "datum": forms.DateInput(attrs={"type": "date"}),
            "vreme": forms.TimeInput(attrs={"type": "time"}),
        }
