from django import forms
from registar.models import Krstenje


class KrstenjeForm(forms.ModelForm):
    class Meta:
        model = Krstenje
        fields = [
            "knjiga",
            "strana",
            "tekuci_broj",
            "anagraf",
            "datum",
            "vreme",
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
            "knjiga": "Протоколарна књига",
            "strana": "Протоколарна страна",
            "tekuci_broj": "Текући број",
            "anagraf": "Анаграф",
            "datum": "Датум крштења",
            "vreme": "Време крштења",
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
