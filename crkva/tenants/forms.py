"""Forms for the self-edit user profile page."""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileForm(forms.ModelForm):
    """Edit first_name, last_name, email of the logged-in user."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Име",
            "last_name": "Презиме",
            "email": "Е-маил",
        }
