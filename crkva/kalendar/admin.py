"""Админ интерфејс за shared Slava модел."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from kalendar.models import Slava


@admin.register(Slava)
class SlavaAdmin(ImportExportMixin, admin.ModelAdmin):
    """Класа админ интерфејса модела Слава."""

    search_fields = (
        "opsti_naziv",
        "naziv",
    )
    list_filter = (
        "mesec",
        "dan",
    )
    list_display = (
        "dan",
        "mesec",
        "mesec_naziv",
        "opsti_naziv",
        "naziv",
    )
    ordering = (
        "mesec",
        "dan",
    )
    list_display_links = ("naziv",)

    @admin.display(description="Назив месеца")
    def mesec_naziv(self, obj):
        """Приказује назив месеца."""
        return obj.get_mesec_naziv()
