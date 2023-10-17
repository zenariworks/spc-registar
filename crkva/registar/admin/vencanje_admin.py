from django.contrib import admin
from import_export.admin import ImportExportMixin


class VencanjeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uid", "z_ime", "n_ime", "aktgod", "knjiga")
    ordering = ("uid",)
