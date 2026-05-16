"""Tenant + Domain + UserMembership models.

Phase 2a: Tenant now subclasses django-tenants' TenantMixin so the
library can create / drop the Postgres schema. A minimal Domain model
(DomainMixin) is added because django-tenants requires TENANT_DOMAIN_MODEL,
even though our routing is session-based (the Domain rows are unused at
runtime; they exist only to satisfy the library's checks).

Phase 2b will move registar tables into per-tenant schemas; until then
the `parohija` FK to `registar.Parohija` still works because both tables
live in `public`.
"""

from __future__ import annotations

import re

from django.conf import settings
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin
from registar.models import Parohija


def _slugify_ascii(value: str) -> str:
    """Cyrillic-friendly slugifier: keep [a-z0-9_], no transliteration."""
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_") or "tenant"


class Tenant(TenantMixin):
    """One parish acting as a tenant in the system.

    Inherits `schema_name` (the Postgres schema name) and the
    auto-create-on-save behaviour from TenantMixin. Save() will create
    the schema via the DATABASE_ROUTERS migration mechanism, unless
    auto_create_schema is False.
    """

    # Inherited from TenantMixin: schema_name (unique CharField)

    parohija = models.OneToOneField(
        Parohija,
        on_delete=models.PROTECT,
        related_name="tenant",
        verbose_name="парохија",
    )
    naziv = models.CharField(
        max_length=200,
        verbose_name="назив тенанта",
        help_text="Кориснички видљив назив (нпр. „Парохија Чукарица“).",
    )
    is_active = models.BooleanField(default=True, verbose_name="активан")
    is_default = models.BooleanField(
        default=False,
        verbose_name="подразумевани",
        help_text="Тенант који видe корисници без експлицитно додељене парохије.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Don't auto-create the schema on save — Phase 2b will manage the
    # initial schema creation explicitly during the data-move migration.
    auto_create_schema = False
    auto_drop_schema = False

    class Meta:
        db_table = "tenants_tenant"
        verbose_name = "Тенант"
        verbose_name_plural = "Тенанти"
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="tenants_tenant_only_one_default",
            ),
        ]

    def __str__(self) -> str:
        return self.naziv

    def save(self, *args, **kwargs):
        if not self.schema_name:
            self.schema_name = (
                _slugify_ascii(self.naziv) or f"tenant_{self.pk or 'new'}"
            )
        super().save(*args, **kwargs)


class Domain(DomainMixin):
    """Required by django-tenants but not actually used for routing.

    Our `SessionTenantMiddleware` picks the tenant from the session,
    not from the request host. We still need this model so
    django-tenants' setup checks pass and `manage.py create_tenant` /
    `tenant_command` keep working in case we use them.
    """

    class Meta:
        db_table = "tenants_domain"
        verbose_name = "Домен"
        verbose_name_plural = "Домени"


class Role(models.TextChoices):
    ADMIN = "admin", "Администратор парохије"
    MEMBER = "member", "Члан парохије"
    VIEWER = "viewer", "Преглед без измена"


class UserMembership(models.Model):
    """Пар User × Tenant — корисник припада једној (или више) парохија."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Тенант у који корисник аутоматски улази после пријаве.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tenants_user_membership"
        verbose_name = "Чланство корисника"
        verbose_name_plural = "Чланства корисника"
        unique_together = [("user", "tenant")]

    def __str__(self) -> str:
        return f"{self.user} → {self.tenant} ({self.get_role_display()})"
