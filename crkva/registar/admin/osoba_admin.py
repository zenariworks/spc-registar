from django.contrib import admin
from import_export.admin import ImportExportMixin
from admin_searchable_dropdown.filters import AutocompleteFilter

class ZanimanjeFilter(AutocompleteFilter):
    title = "Занимање"
    field_name = 'zanimanje'


class OsobaAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ("ime", "prezime", "zanimanje")
    ordering = ("uid",)
    autocomplete_fields = ['zanimanje__naziv']
    search_fields = ['zanimanje__naziv']
    list_filter = [ZanimanjeFilter]
