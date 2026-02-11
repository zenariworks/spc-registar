"""Admin configuration for Mesto model."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Mesto


@admin.register(Mesto)
class MestoAdmin(ImportExportMixin, admin.ModelAdmin):
    """Admin interface for Mesto."""

    list_display = ("naziv",)
    search_fields = ("naziv",)
    ordering = ["naziv"]
