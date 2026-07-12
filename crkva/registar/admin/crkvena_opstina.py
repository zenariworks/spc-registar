"""Модул админ интерфејса модела Црквена општина са опцијама за увоз и извоз."""

from django.contrib import admin
from registar.models import CrkvenaOpstina


@admin.register(CrkvenaOpstina)
class CrkvenaOpstinaAdmin(admin.ModelAdmin):
    """Класа админ интерфејса модела Црквена општина."""

    list_display = ("naziv", "eparhija")
    search_fields = ("naziv", "eparhija__naziv")
    list_filter = ("eparhija",)
