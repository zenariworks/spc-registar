"""
Модул админ интерфејса модела Парохијан са опцијама увоз и извоз.
"""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Osoba


@admin.register(Osoba)
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
    list_select_related = ("adresa",)
    search_fields = [
        "ime",
        "prezime",
        "zanimanje__naziv",
        "narodnost__naziv",
        "adresa__ulica",
        "veroispovest__naziv",
    ]

    def get_full_name(self, obj):
        """Врати пуно име особе."""
        devojacko = f", ({obj.devojacko_prezime})" if obj.devojacko_prezime else ""
        return f"{obj.ime} {obj.prezime}{devojacko}"

    get_full_name.short_description = "Име и Презиме"

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
