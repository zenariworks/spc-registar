from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from registar.models import Mesto


class DrzavaFilter(admin.SimpleListFilter):
    title = _("држава")
    parameter_name = "drzava"

    def lookups(self, request, model_admin):
        drzave = set([m.opstina.drzava for m in Mesto.objects.all()])
        return [(d.uid, d.naziv) for d in drzave]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(mesto__opstina__drzava__uid=self.value())
        return queryset


class OpstinaFilter(admin.SimpleListFilter):
    title = _("општина")
    parameter_name = "opstina"

    def lookups(self, request, model_admin):
        opstine = set([m.opstina for m in Mesto.objects.all()])
        return [(o.uid, o.naziv) for o in opstine]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(mesto__opstina__uid=self.value())
        return queryset


class MestoFilter(admin.SimpleListFilter):
    title = _("место")
    parameter_name = "mesto"

    def lookups(self, request, model_admin):
        return [(m.uid, m.naziv) for m in Mesto.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(mesto__uid=self.value())
        return queryset


class UlicaAdmin(admin.ModelAdmin):
    list_display = ["naziv", "get_mesto", "get_opstina", "get_drzava"]
    list_filter = [DrzavaFilter, OpstinaFilter, MestoFilter]
    search_fields = [
        "naziv",
        "mesto__naziv",
        "mesto__opstina__naziv",
        "mesto__opstina__drzava__naziv",
    ]

    def get_mesto(self, obj):
        return obj.mesto.naziv

    get_mesto.admin_order_field = "mesto"
    get_mesto.short_description = "Место"

    def get_opstina(self, obj):
        return obj.mesto.opstina.naziv

    get_opstina.admin_order_field = "mesto__opstina"
    get_opstina.short_description = "Општина"

    def get_drzava(self, obj):
        return obj.mesto.opstina.drzava.naziv

    get_drzava.admin_order_field = "mesto__opstina__drzava"
    get_drzava.short_description = "Држава"
