from django.contrib import admin
from import_export.admin import ImportExportMixin


class DomacinstvoAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("dom_rbr", "dom_ime", "dom_napom")
    ordering = ("dom_rbr",)
