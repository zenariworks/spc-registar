"""Модул админ интерфејса модела Епархиј са опцијама увоз и извоз."""

from django.contrib import admin
from registar.models import Eparhija

@admin.register(Eparhija)
class EparhijaAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Епархија."""

    list_display = ("naziv", "sediste")
    search_fields = ("naziv", "sediste")
    list_filter = ("sediste",)
    ordering = ("naziv",)
