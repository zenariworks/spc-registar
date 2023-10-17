from django.contrib import admin
from import_export.admin import ImportExportMixin


class SvestenikAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uid", "ime", "zvanje")
    ordering = ("uid",)
