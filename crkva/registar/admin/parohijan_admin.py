from admin_searchable_dropdown.filters import AutocompleteFilter
from django.contrib import admin
from import_export.admin import ImportExportMixin


class ZanimanjeFilter(AutocompleteFilter):
    title = "Занимање"
    field_name = "zanimanje"


class parohijanAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("get_full_name", "datum_rodjenja", "get_zanimanje_naziv")
    ordering = ("datum_rodjenja",)
    autocomplete_fields = ["zanimanje"]
    search_fields = ["ime", "prezime", "zanimanje__naziv"]
    list_filter = [ZanimanjeFilter]

    def get_full_name(self, obj):
        return f"{obj.ime} {obj.prezime}"

    get_full_name.short_description = "Име и Презиме"

    def get_zanimanje_naziv(self, obj):
        return obj.zanimanje.naziv if obj.zanimanje else ""

    get_zanimanje_naziv.short_description = "Занимање"
