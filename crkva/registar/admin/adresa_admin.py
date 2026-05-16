"""Модул админ интерфејса модела Адреса са опцијама за увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Adresa


@admin.register(Adresa)
class AdresaAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Адреса."""

    list_display = ("ulica", "broj", "mesto")
    search_fields = ("ulica", "mesto")
