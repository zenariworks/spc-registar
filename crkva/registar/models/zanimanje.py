"""Модул модела занимања у бази података."""

import uuid

from django.db import models


class Zanimanje(models.Model):
    """Класа која представља занимања."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    sifra = models.CharField(verbose_name="шифра")
    naziv = models.CharField(verbose_name="назив", max_length=255)
    zenski_naziv = models.CharField(verbose_name="женски назив", null=True)

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "zanimanja"
        verbose_name = "Занимање"
        verbose_name_plural = "Занимања"
