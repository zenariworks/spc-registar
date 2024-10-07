"""Модул модела улице у бази података."""

import uuid

from django.db import models

from .drzava import Drzava
from .mesto import Mesto
from .opstina import Opstina
from .svestenik import Svestenik


class Ulica(models.Model):
    """Класа која представља улица."""
    uid = models.IntegerField(primary_key=True, unique=True, editable=False)
    naziv = models.CharField(max_length=255, verbose_name="назив")
    mesto = models.ForeignKey(Mesto, on_delete=models.CASCADE, verbose_name="место")
    opstina = models.ForeignKey(
        Opstina, on_delete=models.CASCADE, verbose_name="општина"
    )
    drzava = models.ForeignKey(Drzava, on_delete=models.CASCADE, verbose_name="држава")

    svestenik = models.ForeignKey(
        Svestenik,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="свештеник",
    )

    def __str__(self):
        return f"{self.naziv}, {self.mesto}, {self.opstina}, {self.drzava}"

    class Meta:
        managed = True
        db_table = "ulice"
        verbose_name = "Улица"
        verbose_name_plural = "Улице"
