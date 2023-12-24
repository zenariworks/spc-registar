from django.contrib import admin

from import_export.admin import ImportExportMixin


class UkucaninAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uid", "ime", "rbrdom")
    ordering = ("uid",)
