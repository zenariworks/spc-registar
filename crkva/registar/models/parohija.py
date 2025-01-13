"""Модул модела парохије у бази података."""

import uuid

from django.db import models

from .crkvena_opstina import CrkvenaOpstina


class Parohija(models.Model):
    """Класа која представља парохија."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=200, verbose_name="назив")
    crkvena_opstina = models.ForeignKey(
        CrkvenaOpstina,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="црквена општина",
    )

    def __str__(self) -> str:
        return f"{'I' if self.naziv == '1' else 'II' if self.naziv == '2' else 'III' if self.naziv == '3' else ''}"

    class Meta:
        managed = True
        db_table: str = "parohije"
        verbose_name: str = "Парохија"
        verbose_name_plural: str = "Парохије"
