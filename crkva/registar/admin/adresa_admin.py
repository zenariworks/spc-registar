"""
Модул админ интерфејса модела Адреса са опцијама за увоз и извоз.
"""

from django.contrib import admin
from registar.models import Adresa


@admin.register(Adresa)
class AdresaAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Адреса."""

    list_display = (
        "ulica",
        "broj",
        "dodatak",
        "postkod",
    )
    search_fields = (
        "ulica",
        "broj",
        "dodatak",
        "postkod",
    )
    list_filter = ("postkod",)
