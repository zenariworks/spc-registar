"""
Модул админ интерфејса модела Занимање са функционалношћу за увоз и извоз.
"""

from django.contrib import admin
from import_export.admin import ImportExportMixin


class ZanimanjeAdmin(ImportExportMixin, admin.ModelAdmin):
    """
    Административни интерфејс за модел занимање са функционалношћу за увоз и извоз.
    """

    list_display = ("sifra", "naziv", "zenski_naziv")
    ordering = ("sifra",)
    search_fields = ["naziv"]
