"""Модул админ интерфејса модела Занимање са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin


class ZanimanjeAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Занимање."""

    list_display = ("sifra", "naziv", "zenski_naziv")
    ordering = ("sifra",)
    search_fields = ["naziv"]
