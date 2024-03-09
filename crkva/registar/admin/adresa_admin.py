from django.contrib import admin


class AdresaAdmin(admin.ModelAdmin):
    list_display = (
        "ulica", "mesto", "opstina", "postanski_broj", "drzava")
    search_fields = (
        "ulica", "mesto", "opstina", "postanski_broj", "drzava")
    list_filter = (
        "opstina", "drzava", "postanski_broj")
