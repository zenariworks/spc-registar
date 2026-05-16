"""Forms for the self-edit user profile page and admin user management."""

from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from tenants.models import Role

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


class AddUserForm(forms.Form):
    """Admin form: create a new user + membership for the active tenant."""

    username = forms.CharField(
        max_length=150,
        label="Корисничко име",
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )
    first_name = forms.CharField(max_length=150, required=False, label="Име")
    last_name = forms.CharField(max_length=150, required=False, label="Презиме")
    email = forms.EmailField(required=False, label="Е-маил")
    password = forms.CharField(
        label="Лозинка", widget=forms.PasswordInput, min_length=8
    )
    role = forms.ChoiceField(choices=Role.choices, label="Улога")
    is_default = forms.BooleanField(
        required=False, initial=True, label="Подразумевани тенант"
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username:
            raise ValidationError("Корисничко име је обавезно.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("Корисник са овим именом већ постоји.")
        return username

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password


class EditRoleForm(forms.Form):
    """Admin form: change a membership's role."""

    role = forms.ChoiceField(choices=Role.choices, label="Улога")
