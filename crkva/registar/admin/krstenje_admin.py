from django.contrib import admin
from import_export.admin import ImportExportMixin


class KrstenjeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = (
        "get_dete_full_name", "datum_krstenja", "mesto_krstenja", "krshram", "get_svestenik_name"
    )
    ordering = ("datum_krstenja",)
    search_fields = ["dete__ime", "dete__prezime", "mesto_krstenja", "krshram", "svestenik__osoba__ime", "svestenik__osoba__prezime"]
    # Add list_filter as needed

    def get_dete_full_name(self, obj):
        return f"{obj.dete.ime} {obj.dete.prezime}"
    get_dete_full_name.short_description = 'Дете'

    def get_svestenik_name(self, obj):
        svestenik_osoba = obj.svestenik.osoba
        return f"{svestenik_osoba.ime} {svestenik_osoba.prezime}" if svestenik_osoba else ''
    get_svestenik_name.short_description = 'Свештеник'
