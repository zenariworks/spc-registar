"""Модул админ интерфејса модела Домаћинство са опцијама увоз и извоз."""

from django.contrib import admin
from import_export.admin import ImportExportMixin


# class DomacinstvoAdmin(ImportExportMixin, admin.ModelAdmin):
#     """Класа админ интерфејса модела Домаћинство."""

#     list_display = (
#         "domacin",
#         "adresa",
#         "tel_fiksni",
#         "tel_mobilni",
#         "slava",
#         "slavska_vodica",
#         "uskrsnja_vodica",
#         "primedba",
#     )
#     ordering = ("domacin",)

#     fieldsets = (
#         ("Основне информације", {"fields": ("domacin", "adresa")}),
#         (
#             "Контакт",
#             {
#                 "fields": ("tel_fiksni", "tel_mobilni"),
#                 "description": "Контакт телефони домаћинства",
#             },
#         ),
#         (
#             "Додатни детаљи",
#             {
#                 "fields": ("slava", ("slavska_vodica", "uskrsnja_vodica"), "primedba"),
#                 "description": "Информације везане за верске објекте",
#             },
#         ),
#     )
