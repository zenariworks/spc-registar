from django.contrib import admin


class NarodnostAdmin(admin.ModelAdmin):
    list_display = ("naziv",)
    search_fields = ("naziv",)
