"""Модул модела укућана у бази података."""

from django.db import models

from .base import TimestampedModel
from .parohijan import Parohijan


class Ukucanin(TimestampedModel):
    """Класа која представља укућана."""

    parohijan = models.ForeignKey(
        Parohijan, on_delete=models.CASCADE, verbose_name="парохијан"
    )

    ime_ukucana = models.CharField(
        max_length=255, verbose_name="име укућана", blank=True, null=True
    )

    def __str__(self) -> str:
        return f"{self.parohijan} - {self.ime_ukucana}"

    class Meta:
        managed = True
        db_table = "ukucani"
        verbose_name = "Укућанин"
        verbose_name_plural = "Укућани"
