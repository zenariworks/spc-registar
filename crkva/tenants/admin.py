"""Django admin for Tenant + UserMembership."""

from django.contrib import admin

from .models import Domain, Tenant, UserMembership


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "naziv",
        "parohija",
        "schema_name",
        "is_active",
        "is_default",
        "created_at",
    )
    list_filter = ("is_active", "is_default")
    search_fields = ("naziv", "schema_name", "parohija__naziv")
    readonly_fields = ("created_at",)


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role", "is_default", "created_at")
    list_filter = ("tenant", "role", "is_default")
    search_fields = ("user__username", "tenant__naziv")
    raw_id_fields = ("user",)


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain",)
