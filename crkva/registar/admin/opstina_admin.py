"""Admin configuration for Opstina model."""

from django.contrib import admin
from import_export.admin import ImportExportMixin
from registar.models import Opstina


@admin.register(Opstina)
class OpstinaAdmin(ImportExportMixin, admin.ModelAdmin):
    """Admin interface for Opstina."""

    list_display = ("naziv",)
    search_fields = ("naziv",)
    ordering = ["naziv"]
