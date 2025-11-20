"""Django форма за унос вероисповести."""

from django.forms import ModelForm
from registar.models import Veroispovest


class VeroispovestForm(ModelForm):
    """Формулар за унос и измену вероисповести."""

    class Meta:
        model = Veroispovest
        fields = ["naziv"]
