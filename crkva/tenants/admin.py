"""Django admin for Zakupac + Clanstvo."""

from django.contrib import admin

from .models import Clanstvo, Domen, Zakupac


@admin.register(Zakupac)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "naziv",
        "mesto",
        "schema_name",
        "default_phone_region",
        "is_active",
        "is_default",
        "created_at",
    )
    list_filter = ("is_active", "is_default", "default_phone_region")
    search_fields = ("naziv", "schema_name")
    readonly_fields = ("created_at",)


@admin.register(Clanstvo)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ("korisnik", "parohija", "uloga", "is_default", "created_at")
    list_filter = ("parohija", "uloga", "is_default")
    search_fields = ("korisnik__username", "parohija__naziv")
    raw_id_fields = ("korisnik",)


@admin.register(Domen)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain",)
