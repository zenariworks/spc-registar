"""
Модул админ интерфејса модела Укућанин са опцијама увоз и извоз.
"""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Ukucanin


@admin.register(Ukucanin)
class UkucaninAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Укућанин."""

    list_select_related = ("domacinstvo", "domacinstvo__domacin", "osoba")
    list_display = ("domacinstvo", "osoba", "ime_ukucana", "uloga", "preminuo")
    list_filter = ("uloga", "preminuo")
    # Сортирај по имену домаћина + укућанина, не по сировом FK id-у (#340).
    ordering = ["domacinstvo__domacin__prezime", "ime_ukucana"]
    search_fields = ("osoba__ime", "osoba__prezime", "ime_ukucana")
