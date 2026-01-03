"""Модул админ интерфејса модела Народност са опцијама увоз и извоз."""

from django.contrib import admin
from registar.models import Narodnost


@admin.register(Narodnost)
class NarodnostAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Народност."""

    list_display = ("naziv",)
    search_fields = ("naziv",)
