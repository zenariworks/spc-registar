from django.contrib import admin
from import_export.admin import ImportExportMixin


class SvestenikAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("sv_rbr", "sv_ime", "sv_zvanje")
    ordering = ("sv_rbr",)
