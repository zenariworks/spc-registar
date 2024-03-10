from admin_searchable_dropdown.filters import AutocompleteFilter
from django.contrib import admin
from import_export.admin import ImportExportMixin


class ZanimanjeFilter(AutocompleteFilter):
    title = "Занимање"
    field_name = "zanimanje"


class ParohijanAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "get_full_name",
        "mesto_rodjenja",
        "datum_rodjenja",
        "pol",
        "get_zanimanje_naziv",
        "narodnost",
        "adresa",
    )
    ordering = ("datum_rodjenja",)
    autocomplete_fields = ["zanimanje", "adresa", "narodnost", "veroispovest"]
    search_fields = [
        "ime",
        "prezime",
        "zanimanje__naziv",
        "narodnost__naziv",
        "adresa__naziv",
        "veroispovest",
    ]
    list_filter = [ZanimanjeFilter]

    def get_full_name(self, obj):
        return f"{obj.ime} {obj.prezime}"

    get_full_name.short_description = "Име и Презиме"

    def get_zanimanje_naziv(self, obj):
        return obj.zanimanje.naziv if obj.zanimanje else ""

    get_zanimanje_naziv.short_description = "Занимање"

    fieldsets = (
        (None, {"fields": ("ime", "prezime", "pol")}),
        (
            "Рођење и место",
            {
                "fields": (
                    "mesto_rodjenja",
                    "datum_rodjenja",
                    "vreme_rodjenja",
                )
            },
        ),
        (
            "Додатне информације",
            {
                "fields": (
                    "devojacko_prezime",
                    "zanimanje",
                    "veroispovest",
                    "narodnost",
                )
            },
        ),
    )
    readonly_fields = ("uid",)
