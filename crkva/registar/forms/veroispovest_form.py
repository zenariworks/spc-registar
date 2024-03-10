from django.forms import ModelForm
from registar.models import Veroispovest


class VeroispovestForm(ModelForm):
    class Meta:
        model = Veroispovest
        fields = ["naziv"]
