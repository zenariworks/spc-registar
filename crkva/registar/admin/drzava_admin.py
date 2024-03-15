from django.contrib import admin


class DrzavaAdmin(admin.ModelAdmin):
    list_display = ("naziv", "postkod_regex")
    search_fields = ["naziv"]
