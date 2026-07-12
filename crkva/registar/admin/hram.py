"""Модул админ интерфејса модела Храм са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Hram


@admin.register(Hram)
class HramAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Храм."""

    search_fields = ("naziv",)
