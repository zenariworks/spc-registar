from django.contrib import admin


class CrkvenaOpstinaAdmin(admin.ModelAdmin):
    list_display = ("naziv", "eparhija")
    search_fields = ("naziv", "eparhija__naziv")
    list_filter = ("eparhija",)
