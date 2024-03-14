from django.contrib import admin


class AdresaAdmin(admin.ModelAdmin):
    list_display = ("ulica",)
    search_fields = ("ulica",)
    # list_filter = ("opstina", "drzava", "postanski_broj")
