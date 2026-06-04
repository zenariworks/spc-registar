"""Tenant + Domain + UserMembership models — Phase 2b.

Phase 2b: registar moves to TENANT_APPS, so its tables (including Parohija)
live in per-tenant schemas. A FK from `public.tenants_tenant` to
`crkva_sv_petke_cukarica.parohije` is impossible to model cleanly in Postgres,
so `Tenant.parohija` was replaced with a plain `parohija_naziv` CharField.

`auto_create_schema = True` so creating a Tenant row automatically
creates the corresponding Postgres schema and runs TENANT_APPS migrations
against it.
"""

from __future__ import annotations

import re

from django.conf import settings
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


def _slugify_ascii(value: str) -> str:
    """Cyrillic-friendly slugifier: keep [a-z0-9_], no transliteration."""
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_") or "tenant"


class Tenant(TenantMixin):
    """One parish acting as a tenant. Owns a Postgres schema."""

    # Inherited from TenantMixin: schema_name (unique CharField + validator)

    naziv = models.CharField(
        max_length=200,
        verbose_name="назив парохије",
        help_text="Кориснички видљив назив (нпр. „Парохија Чукарица“).",
    )
    parohija_naziv = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="парохија (име)",
        help_text="Име парохије за приказ. У свакој парохијској шеми "
        "постоји сопствена Parohija инстанца; ово је само display label.",
    )
    default_phone_region = models.CharField(
        max_length=2,
        default="RS",
        verbose_name="подразумевана земља за телефон",
        help_text="ISO 3166-1 alpha-2 (нпр. RS, NL, DE, AT, CH). "
        "Када корисник укуца локални број без +префикса, "
        "систем користи овај код за тумачење.",
    )
    is_active = models.BooleanField(default=True, verbose_name="активан")
    is_default = models.BooleanField(
        default=False,
        verbose_name="подразумевани",
        help_text="Парохија коју виде корисници без експлицитно додељене парохије.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Creating a Tenant row auto-creates its Postgres schema and runs
    # TENANT_APPS migrations against it.
    auto_create_schema = True
    auto_drop_schema = False  # Manual drop only — protects against accidents.

    class Meta:
        db_table = "tenants_tenant"
        verbose_name = "Парохија"
        verbose_name_plural = "Парохије"
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
    """Required by django-tenants for setup, but not used at runtime
    (we route by session, not by host)."""

    class Meta:
        db_table = "tenants_domain"
        verbose_name = "Домен"
        verbose_name_plural = "Домени"


class Role(models.TextChoices):
    # Канцеларија editirá parohijane/domaćinstva/krštenja/venčanja.
    # Свештенство editirá svestenike. Преглед је read-only за све.
    ADMIN = "admin", "Администратор"
    KANCELARIJA = "kancelarija", "Канцеларија"
    SVESTENSTVO = "svestenstvo", "Свештенство"
    PREGLED = "pregled", "Преглед"


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
        default=Role.PREGLED,
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Парохија у коју корисник аутоматски улази после пријаве.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="активно чланство",
        help_text="Деактивирано чланство закључава корисника из ове парохије, "
        "али не утиче на глобални налог нити на приступ другим парохијама.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tenants_user_membership"
        verbose_name = "Чланство корисника"
        verbose_name_plural = "Чланства корисника"
        unique_together = [("user", "tenant")]

    def __str__(self) -> str:
        return f"{self.user} → {self.tenant} ({self.get_role_display()})"
