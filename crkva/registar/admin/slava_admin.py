from django.contrib import admin
from import_export.admin import ImportExportMixin


class SlavaAdmin(ImportExportMixin, admin.ModelAdmin):
    #     search_fields = ('naziv', 'sediste')
    # list_filter = ('sediste',)
    search_fields = (
        "opsti_naziv",
        "naziv",
    )
    list_filter = (
        "mesec",
        "dan",
    )
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
