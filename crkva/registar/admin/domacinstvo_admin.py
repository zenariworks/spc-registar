from django.contrib import admin
from import_export.admin import ImportExportMixin


class DomacinstvoAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "domacin",
        "adresa",
        "tel_fiksni",
        "tel_mobilni",
        "slava",
        "napomena",
    )
    ordering = ("domacin",)
