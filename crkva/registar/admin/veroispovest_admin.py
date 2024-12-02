"""Модул админ интерфејса модела Вероисповест са опцијама увоз и извоз."""

from django.contrib import admin
from registar.models import Veroispovest

@admin.register(Veroispovest)
class VeroispovestAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Вероисповест."""

    search_fields = ["naziv"]
