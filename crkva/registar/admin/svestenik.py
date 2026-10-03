"""Модул админ интерфејса модела Свештеник са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Svestenik


@admin.register(Svestenik)
class SvestenikAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Свештеник."""

    list_select_related = ("parohija", "user")
    list_display = ("get_full_name", "zvanje", "get_parohija", "user")
    ordering = ("prezime", "ime")
    raw_id_fields = ("user",)

    @admin.display(
        description="Име и презиме",
        ordering="ime",
    )
    def get_full_name(self, obj):
        return f"{obj.ime} {obj.prezime}"

    @admin.display(
        description="Парохија",
        ordering="parohija__naziv",
    )
    def get_parohija(self, obj):
        return obj.parohija.naziv if obj.parohija else "Нема"
