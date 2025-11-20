"""Форме за претрагу."""

from django import forms


class SearchForm(forms.Form):
    """Форма за претрагу по тексту."""

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
