"""Модул модела занимања у бази података."""

from django.db import models
from registar.models._naziv import NazivModel


class Zanimanje(NazivModel):
    """Класа која представља занимања."""

    sifra = models.CharField(verbose_name="шифра", max_length=50)
    naziv = models.CharField(verbose_name="назив", max_length=255)
    zenski_naziv = models.CharField(
        verbose_name="женски назив", max_length=255, null=True
    )

    class Meta(NazivModel.Meta):
        db_table = "zanimanja"
        verbose_name = "Занимање"
        verbose_name_plural = "Занимања"
