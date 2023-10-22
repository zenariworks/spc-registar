from django.contrib import admin
from import_export.admin import ImportExportMixin


class SvestenikAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uid", "parohija", "zvanje")
    ordering = ("uid",)
