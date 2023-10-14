from django.contrib import admin
from import_export.admin import ImportExportMixin


class VencanjeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("v_rbr", "v_z_ime", "v_n_ime", "v_aktgod", "v_knjiga")
    ordering = ("v_rbr",)
