"""Модул админ интерфејса модела Крштење са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Krstenje


@admin.register(Krstenje)
class KrstenjeAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Крштење."""

    ordering = ("datum",)
    list_display = (
        "redni_broj_krstenja_tekuca_godina",
        "krstenje_tekuca_godina",
        "knjiga",
        "broj",
        "strana",
        "datum",
        "vreme",
        "mesto",
        "hram",
        # Особе (FK)
        "dete",
        "otac",
        "majka",
        "kum",
        "svestenik",
        # Адресе (специфичне за догађај)
        "adresa_deteta_grad",
        "adresa_deteta_ulica",
        "adresa_deteta_broj",
        "gradjansko_ime_deteta",
        "adresa_oca_mesto",
        "adresa_majke_mesto",
        # Остали подаци о детету
        "dete_rodjeno_zivo",
        "dete_po_redu_po_majci",
        "dete_vanbracno",
        "dete_blizanac",
        "drugo_dete_blizanac_ime",
        "dete_sa_telesnom_manom",
        # Кум адреса
        "adresa_kuma_mesto",
        # Регистрација
        "mesto_registracije",
        "datum_registracije",
        "maticni_broj",
        "strana_registracije",
        "primedba",
    )
    fieldsets = ((None, {"fields": ("knjiga", "broj", "strana")}),)
    readonly_fields = ("uid",)
