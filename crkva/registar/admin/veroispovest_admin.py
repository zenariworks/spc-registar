from django.contrib import admin


class VeroispovestAdmin(admin.ModelAdmin):
    search_fields = ["naziv"]
