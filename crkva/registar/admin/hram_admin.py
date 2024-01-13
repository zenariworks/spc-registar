from django.contrib import admin

from import_export.admin import ImportExportMixin


class HramAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("naziv", "adresa")
    search_fields = ("naziv",)
