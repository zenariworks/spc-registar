# forms.py
from django import forms


class SearchForm(forms.Form):
    search = forms.CharField(
        label="Претрага",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "type": "search",
                "placeholder": "Филтер за претрагу",
                "class": "search-input",
                "aria-label": "Филтер за претрагу",
            }
        ),
    )
