# forms.py
from django import forms
from django.forms import ModelForm

from .models import Veroispovest


class SearchForm(forms.Form):
    query = forms.CharField(label="Search", max_length=100)


class VeroispovestForm(ModelForm):
    class Meta:
        model = Veroispovest
        fields = ["naziv"]
