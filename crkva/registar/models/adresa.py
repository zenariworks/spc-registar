"""Модул модела адресе у бази података."""

import uuid

from django.db import models
from django.db.models.functions import Lower
from simple_history.models import HistoricalRecords


class Adresa(models.Model):
    """Класа која представља адресе."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    ulica = models.CharField(
        max_length=255, verbose_name="улица", blank=True, default=""
    )
    broj = models.CharField(max_length=20, verbose_name="број", blank=True, default="")
    sprat = models.CharField(
        max_length=10, verbose_name="спрат", blank=True, default=""
    )
    broj_stana = models.CharField(
        max_length=10, verbose_name="број стана", blank=True, default=""
    )
    mesto = models.CharField(
        max_length=100, verbose_name="место", blank=True, default="", db_index=True
    )
    postkod = models.CharField(
        max_length=10, verbose_name="поштански број", blank=True, default=""
    )
    primedba = models.TextField(blank=True, default="", verbose_name="примедба")

    # Street -> priest assignment (issue #26). The parish territory is split
    # among priests by street; this drives the Easter-water (васкршња водица)
    # route-planning report. String ref avoids a circular import (Svestenik
    # already imports Adresa for its own FK).
    svestenik = models.ForeignKey(
        "registar.Svestenik",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adrese",
        verbose_name="свештеник (улица)",
        help_text="Свештеник задужен за ову улицу (за васкршњу водицу).",
    )

    history = HistoricalRecords(user_db_constraint=False)

    def __str__(self):
        parts = [self.ulica, self.broj]
        if self.sprat:
            parts.append(f"спрат {self.sprat}")
        if self.broj_stana:
            parts.append(f"стан {self.broj_stana}")
        result = " ".join(p for p in parts if p)
        if self.mesto:
            result = f"{result}, {self.mesto}" if result else self.mesto
        return result or "—"

    class Meta:
        managed = True
        db_table = "adrese"
        verbose_name = "Адреса"
        verbose_name_plural = "Адресе"
        indexes = [
            models.Index(fields=["ulica", "broj"], name="adresa_ulica_broj_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower("ulica"),
                Lower("broj"),
                Lower("broj_stana"),
                Lower("mesto"),
                name="unique_adresa_normalized",
            ),
        ]
