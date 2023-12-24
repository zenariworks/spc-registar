from django.contrib import admin

from import_export.admin import ImportExportMixin


class SvestenikAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("get_full_name", "zvanje", "parohija")
    ordering = ("osoba__prezime", "osoba__ime")

    def get_full_name(self, obj):
        return f"{obj.osoba.ime} {obj.osoba.prezime}"
    get_full_name.short_description = 'Име и презиме'
    get_full_name.admin_order_field = 'osoba__ime'
