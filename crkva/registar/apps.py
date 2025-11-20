"""Конфигурација Django апликације регистар."""

from django.apps import AppConfig


class RegistarConfig(AppConfig):
    """Конфигурација за Django апликацију регистар."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "registar"
