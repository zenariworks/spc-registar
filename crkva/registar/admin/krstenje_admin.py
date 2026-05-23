"""Модул админ интерфејса модела Крштење са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Krstenje


@admin.register(Krstenje)
class KrstenjeAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Крштење."""

    ordering = ("datum",)
    list_display = (
        "redni_broj",
        "godina_registracije",
        "knjiga",
        "broj",
        "strana",
        "datum",
        "vreme",
        "hram",
        # Особе (FK)
        "dete",
        "otac",
        "majka",
        "kum",
        "svestenik",
        # Остали подаци о детету
        "zivorodjeno",
        "po_redu",
        "vanbracno",
        "blizanac",
        "ime_blizanca",
        "telesna_mana",
        # Регистрација
        "mesto_registracije",
        "datum_registracije",
        "maticni_broj",
        "strana_registracije",
        "primedba",
    )
    fieldsets = ((None, {"fields": ("knjiga", "broj", "strana")}),)
    readonly_fields = ("uid",)
