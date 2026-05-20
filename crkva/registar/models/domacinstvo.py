"""Модул модела домаћинства у бази података."""

import uuid

from django.db import models
from kalendar.models import Slava
from model_utils.models import TimeStampedModel
from registar.fields import TenantPhoneNumberField
from simple_history.models import HistoricalRecords

from .adresa import Adresa
from .parohijan import Osoba


class Domacinstvo(TimeStampedModel):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    domacin = models.OneToOneField(
        Osoba,
        on_delete=models.CASCADE,
        verbose_name="домаћин",
        related_name="domacinstvo",
    )

    adresa = models.ForeignKey(
        Adresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="адреса домаћинства",
    )

    slava = models.ForeignKey(
        Slava,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        # Cross-schema FK: Slava lives in the public schema; Postgres cannot
        # enforce FK constraints across schemas in django-tenants, so we drop
        # the DB-level constraint and keep only the Python-level relationship.
        db_constraint=False,
        verbose_name="слава домаћинства",
    )

    tel_fiksni = TenantPhoneNumberField(
        blank=True, null=True, verbose_name="фиксни телефон"
    )
    tel_mobilni = TenantPhoneNumberField(
        blank=True, null=True, verbose_name="мобилни телефон"
    )
    slavska_vodica = models.BooleanField(default=False)
    vaskrsnja_vodica = models.BooleanField(default=False)
    napomena = models.TextField(blank=True, null=True)

    history = HistoricalRecords()

    class Meta:
        db_table = "domacinstva"
        verbose_name = "Домаћинство"
        verbose_name_plural = "Домаћинства"

    def __str__(self):
        return f"Домаћинство {self.domacin.prezime}"
