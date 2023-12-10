from django.contrib import admin
from import_export.admin import ImportExportMixin


class ZanimanjeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("sifra", "naziv", "zenski_naziv")
    ordering = ("sifra",)
    search_fields = ["naziv"]
