from django.contrib import admin
from import_export.admin import ImportExportMixin


class KrstenjeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("k_rbr", "k_datum", "k_mesto", "k_ulica", "k_broj")
    ordering = ("k_rbr",)
