from django.contrib import admin
from import_export.admin import ImportExportMixin


class UkucaninAdmin(ImportExportMixin, admin.ModelAdmin):
    """
    Административни интерфејс за модел укућанин са функционалношћу за увоз и извоз.
    """

    list_display = ("parohijan", "domacinstvo", "uloga")
    ordering = ["parohijan"]
