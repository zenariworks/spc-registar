from django.contrib import admin

from import_export.admin import ImportExportMixin


class SlavaAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "dan",
        "mesec",
        "opsti_naziv",
        "naziv",
    )
    ordering = (
        "mesec",
        "dan",
    )
    list_display_links = ("naziv",)
