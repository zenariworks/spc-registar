"""Модул админ интерфејса модела Дрзава са опцијама увоз и извоз."""

from django.contrib import admin


class DrzavaAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Дрзава."""

    list_display = ("naziv", "postkod_regex")
    search_fields = ["naziv"]
