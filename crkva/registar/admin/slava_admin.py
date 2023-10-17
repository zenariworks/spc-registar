from django.contrib import admin
from import_export.admin import ImportExportMixin


class SlavaAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("uid", "назив")
    ordering = ("uid",)
