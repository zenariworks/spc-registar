"""Модул админ интерфејса модела Крштење са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin


class KrstenjeAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Крштење."""

    ordering = ("datum",)
    fieldsets = (
        (None, {"fields": ("knjiga", "broj", "strana")}),
    )
    readonly_fields = ("uid",)
