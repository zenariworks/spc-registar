"""Модул модела адресе у бази података."""

import uuid

from django.db import models
from django.db.models.functions import Lower


class Adresa(models.Model):
    """Класа која представља адресе."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    ulica = models.CharField(
        max_length=255, verbose_name="улица", blank=True, default=""
    )
    broj = models.CharField(max_length=10, verbose_name="број", blank=True, default="")
    sprat = models.CharField(
        max_length=10, verbose_name="спрат", blank=True, default=""
    )
    broj_stana = models.CharField(
        max_length=10, verbose_name="број стана", blank=True, default=""
    )
    mesto = models.CharField(
        max_length=100, verbose_name="место", blank=True, default=""
    )
    postkod = models.CharField(
        max_length=10, verbose_name="поштански број", blank=True, default=""
    )
    primedba = models.TextField(blank=True, default="", verbose_name="примедба")

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
        constraints = [
            models.UniqueConstraint(
                Lower("ulica"),
                Lower("broj"),
                Lower("broj_stana"),
                Lower("mesto"),
                name="unique_adresa_normalized",
            ),
        ]
