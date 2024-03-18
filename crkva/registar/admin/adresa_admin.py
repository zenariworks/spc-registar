from django.contrib import admin


class AdresaAdmin(admin.ModelAdmin):
    list_display = (
        "ulica",
        "broj",
        "dodatak",
        "postkod",
    )
    search_fields = (
        "ulica",
        "broj",
        "dodatak",
        "postkod",
    )
    list_filter = ("postkod",)
