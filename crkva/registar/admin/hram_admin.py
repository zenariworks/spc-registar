"""Модул админ интерфејса модела Храм са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin


class HramAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Храм."""

    #list_display = ("naziv")
    search_fields = ("naziv",)
