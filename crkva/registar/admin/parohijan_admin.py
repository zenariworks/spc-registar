"""Модул админ интерфејса модела Парохијан са опцијама увоз и извоз."""

from admin_searchable_dropdown.filters import AutocompleteFilter
from django.contrib import admin
from import_export.admin import ImportExportMixin


# class ZanimanjeFilter(AutocompleteFilter):
#     title = "Занимање"
#     field_name = "zanimanje"


class ParohijanAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Парохија."""

    list_display = (
        "get_full_name",
        "mesto_rodjenja",
        "datum_rodjenja",
        "pol",
        "adresa",
    )
    ordering = ("datum_rodjenja",)
    autocomplete_fields = ["adresa"]
    search_fields = [
        "ime",
        "prezime",
        "zanimanje",
        "narodnost",
        "adresa__naziv",
        "veroispovest",
    ]
    #list_filter = [ZanimanjeFilter]

    def get_full_name(self, obj):
        devojacko = f", ({obj.devojacko_prezime})" if obj.devojacko_prezime else ""
        return f"{obj.ime} {obj.prezime}{devojacko}"

    get_full_name.short_description = "Име и Презиме"

    # def get_zanimanje_naziv(self, obj):
    #     return obj.zanimanje.naziv if obj.zanimanje else ""

    # get_zanimanje_naziv.short_description = "Занимање"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "pol",
                    "ime",
                    "prezime",
                    "devojacko_prezime",
                )
            },
        ),
        (
            "Рођење и место",
            {
                "fields": (
                    "mesto_rodjenja",
                    ("datum_rodjenja", "vreme_rodjenja"),
                )
            },
        ),
        (
            "Додатне информације",
            {
                "fields": (
                    "zanimanje",
                    "veroispovest",
                    "narodnost",
                )
            },
        ),
    )
    readonly_fields = ("uid",)
