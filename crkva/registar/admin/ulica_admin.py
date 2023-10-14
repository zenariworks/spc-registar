from django.contrib import admin
from import_export.admin import ImportExportMixin


class UlicaAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("ul_rbr", "ul_naziv", "ul_rbrsv")
    ordering = ("ul_rbr",)
