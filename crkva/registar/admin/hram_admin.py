from django.contrib import admin
from import_export.admin import ImportExportMixin


class HramAdmin(ImportExportMixin, admin.ModelAdmin):
    """
    Административни интерфејс за модел храма са функционалношћу за увоз и извоз.
    """

    list_display = ("naziv", "adresa")
    search_fields = ("naziv",)
