"""Модул модела занимања у бази података."""

import uuid

from django.db import models
from django.db.models.functions import Lower

from registar.text_utils import normalize_naziv


class Zanimanje(models.Model):
    """Класа која представља занимања."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    sifra = models.CharField(verbose_name="шифра")
    naziv = models.CharField(verbose_name="назив", max_length=255)
    zenski_naziv = models.CharField(verbose_name="женски назив", null=True)

    def __str__(self):
        return f"{self.naziv}"

    def save(self, *args, **kwargs):
        # Нормализуј назив да case-insensitive ограничење не пропусти
        # дупликате са вишком размака (#252).
        if self.naziv:
            self.naziv = normalize_naziv(self.naziv)
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("naziv"), name="zanimanje_naziv_ci_uniq"
            ),
        ]
        db_table = "zanimanja"
        verbose_name = "Занимање"
        verbose_name_plural = "Занимања"
