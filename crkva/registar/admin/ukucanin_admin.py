"""Модул админ интерфејса модела Укућанин са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin


class UkucaninAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Укућанин."""

    list_display = ("parohijan", "domacinstvo", "uloga")
    ordering = ["parohijan"]
