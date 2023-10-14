from django.contrib import admin
from import_export.admin import ImportExportMixin


class UkucaninAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uk_rbr", "uk_ime", "uk_rbrdom")
    ordering = ("uk_rbr",)
