"""Модул админ интерфејса модела Крштење са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin


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
        "adresa_deteta_grad",
        "adresa_deteta_ulica",
        "adresa_deteta_broj",
        "datum_rodjenja",
        "vreme_rodjenja",
        "mesto_rodjenja",
        "ime_deteta",
        "gradjansko_ime_deteta",
        "pol_deteta",
        "ime_oca",
        "prezime_oca",
        "zanimanje_oca",
        "adresa_oca_mesto",
        "veroispovest_oca",
        "narodnost_oca",
        "ime_majke",
        "prezime_majke",
        "zanimanje_majke",
        "adresa_majke_mesto",
        "dete_rodjeno_zivo",
        "dete_po_redu_po_majci",
        "dete_vanbracno",
        "dete_blizanac",
        "drugo_dete_blizanac_ime",
        "dete_sa_telesnom_manom",
        "svestenik",
        "ime_kuma",
        "prezime_kuma",
        "zanimanje_kuma",
        "adresa_kuma_mesto",
        "mesto_registracije",
        "datum_registracije",
        "maticni_broj",
        "strana_registracije",
        "primedba",
    )
    fieldsets = ((None, {"fields": ("knjiga", "broj", "strana")}),)
    readonly_fields = ("uid",)
