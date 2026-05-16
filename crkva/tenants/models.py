"""Tenant + UserMembership models.

Phase 1: foundation. These are plain Django models — no django-tenants
integration yet. The `Tenant` row simply names a parish-as-tenant and
will get a `schema_name` once we enable per-schema isolation in Phase 2.

Today:
  - Every Tenant wraps one `Parohija`.
  - Every authenticated User has exactly one active UserMembership; the
    middleware reads it on each request and exposes it as `request.tenant`.
  - Nothing scopes queries by tenant yet — that comes in Phase 2.
"""

from __future__ import annotations

import re

from django.conf import settings
from django.db import models
from registar.models import Parohija


def _slugify_ascii(value: str) -> str:
    """Cyrillic-friendly slugifier: keep [a-z0-9_], no transliteration."""
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_") or "tenant"


class Tenant(models.Model):
    """One parish acting as a tenant in the system.

    `schema_name` is reserved for Phase 2 when each tenant gets its own
    Postgres schema. Until then it's informational.
    """

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
    schema_name = models.CharField(
        max_length=63,
        unique=True,
        verbose_name="schema name",
        help_text="Postgres schema име за изолацију података. "
        "Реално користи се од Фазе 2.",
    )
    is_active = models.BooleanField(default=True, verbose_name="активан")
    is_default = models.BooleanField(
        default=False,
        verbose_name="подразумевани",
        help_text="Тенант који видe корисници без експлицитно додељене парохије.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

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
