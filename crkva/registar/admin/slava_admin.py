from django.contrib import admin
from import_export.admin import ImportExportMixin


class SlavaAdmin(ImportExportMixin, admin.ModelAdmin):
    """
    Административни интерфејс за модел слава са функционалношћу за увоз и извоз.
    """

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
        "opsti_naziv",
        "naziv",
    )
    ordering = (
        "mesec",
        "dan",
    )
    list_display_links = ("naziv",)
