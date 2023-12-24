from django.contrib import admin

from import_export.admin import ImportExportMixin


class DomacinstvoAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uid", "ime", "napomena")
    ordering = ("uid",)
