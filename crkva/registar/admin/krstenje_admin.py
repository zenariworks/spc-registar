from django.contrib import admin
from import_export.admin import ImportExportMixin


class KrstenjeAdmin(ImportExportMixin, admin.ModelAdmin):
    """
    Административни интерфејс за модел крштења са функционалношћу за увоз и извоз.
    """

    list_display = (
        "get_dete_full_name",
        "datum",
        "get_hram_naziv",
        "get_svestenik_name",
    )
    ordering = ("datum",)
    search_fields = [
        "dete__ime",
        "dete__prezime",
        "hram__naziv",
        "svestenik__parohijan__ime",
        "svestenik__parohijan__prezime",
    ]
    fieldsets = (
        (None, {"fields": (("knjiga", "strana", "tekuci_broj"), "anagraf")}),
        (
            "Детаљи крштења",
            {
                "fields": (
                    ("datum", "vreme", "hram"),
                    "dete",
                    (
                        "otac",
                        "majka",
                    ),
                    ("blizanac", "dete_majci", "dete_bracno", "mana"),
                    "svestenik",
                    "kum",
                    "primedba",
                )
            },
        ),
    )
    readonly_fields = ("uid",)

    def get_dete_full_name(self, obj):
        """
        Враћа пуно име детета.
        """
        return f"{obj.dete.ime} {obj.dete.prezime}"

    get_dete_full_name.short_description = "Дете"

    def get_hram_naziv(self, obj):
        """
        Враћа назив храма.
        """
        return obj.hram.naziv

    get_hram_naziv.short_description = "Храм"

    def get_svestenik_name(self, obj):
        """
        Враћа име и презиме свештеника ако постоји.
        """
        return f"{obj.svestenik.ime} {obj.svestenik.prezime}" if obj.svestenik else ""

    get_svestenik_name.short_description = "Свештеник"
