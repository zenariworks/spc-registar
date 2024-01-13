from django.contrib import admin
from import_export.admin import ImportExportMixin

class SvestenikAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("get_full_name", "zvanje", "get_parohija")
    ordering = ("prezime", "ime")

    def get_full_name(self, obj):
        return f"{obj.ime} {obj.prezime}"
    get_full_name.short_description = 'Име и презиме'
    get_full_name.admin_order_field = 'ime'

    def get_parohija(self, obj):
        return obj.parohija.naziv if obj.parohija else 'Нема'
    get_parohija.short_description = 'Парохија'
    get_parohija.admin_order_field = 'parohija__naziv'
