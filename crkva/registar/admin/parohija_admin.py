from django.contrib import admin


class ParohijaAdmin(admin.ModelAdmin):
    list_display = (
        "naziv",
        "crkvena_opstina",
    )
    search_fields = (
        "naziv",
        "crkvena_opstina__naziv",
    )
    list_filter = ("crkvena_opstina",)
