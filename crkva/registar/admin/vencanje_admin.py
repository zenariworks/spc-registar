"""Модул админ интерфејса модела Венчање са опцијама увоз и извоз."""

from django.contrib import admin
from registar.models import Vencanje


@admin.register(Vencanje)
class VencanjeAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Венчање."""

    list_display = (
        "knjiga_strana_broj",
        "zenik",
        "nevesta",
        "datum",
        "svestenik",
        "hram",
    )

    def knjiga_strana_broj(self, obj):
        return f"{obj.knjiga}.{obj.strana}.{obj.tekuci_broj}"

    knjiga_strana_broj.short_description = "Књига.страна.број"

    fieldsets = (
        (None, {"fields": (("knjiga", "strana", "tekuci_broj"),)}),
        (
            "Информације о венчању",
            {
                "fields": (
                    "datum",
                    ("zenik", "zenik_rb_brak"),
                    ("nevesta", "nevesta_rb_brak"),
                    "datum_ispita",
                )
            },
        ),
        (
            "Породичне информације",
            {"fields": (("tast", "tasta"), ("svekar", "svekrva"))},
        ),
        (
            "Детаљи церемоније",
            {
                "fields": (
                    "hram",
                    "svestenik",
                    "kum",
                    "stari_svat",
                    "primedba",
                )
            },
        ),
    )
    readonly_fields = ("uid",)
