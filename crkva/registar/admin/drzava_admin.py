"""Модул админ интерфејса модела Дрзава са опцијама увоз и извоз."""

from django.contrib import admin
from registar.models import Drzava

@admin.register(Drzava)
class DrzavaAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Дрзава."""

    list_display = ("naziv", "postkod_regex")
    search_fields = ["naziv"]
