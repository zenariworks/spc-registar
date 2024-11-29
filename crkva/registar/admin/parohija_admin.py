"""Модул админ интерфејса модела Парохија са опцијама увоз и извоз."""

from django.contrib import admin
from registar.models import Parohija

@admin.register(Parohija)
class ParohijaAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Парохија."""

    list_display = (
        "naziv",
        "crkvena_opstina",
    )
    search_fields = (
        "naziv",
        "crkvena_opstina__naziv",
    )
    list_filter = ("crkvena_opstina",)
