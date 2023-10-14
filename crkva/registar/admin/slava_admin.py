from django.contrib import admin
from import_export.admin import ImportExportMixin


class SlavaAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("sl_rbr", "sl_naziv", "sl_dan", "sl_mesec")
    ordering = ("sl_rbr",)
