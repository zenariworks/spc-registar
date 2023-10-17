from django.contrib import admin
from import_export.admin import ImportExportMixin


class KrstenjeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uid", "datum", "mesto", "ulica", "broj")
    ordering = ("uid",)
