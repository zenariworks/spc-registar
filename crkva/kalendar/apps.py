"""Django app config for the shared kalendar package."""

from django.apps import AppConfig


class KalendarConfig(AppConfig):
    """Configuration for the kalendar app (shared across all tenants)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "kalendar"
    verbose_name = "Календар"
