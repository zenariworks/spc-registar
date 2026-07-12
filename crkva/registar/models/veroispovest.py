"""Модул модела вероисповести у бази података."""

import uuid

from django.db import models
from django.db.models.functions import Lower
from registar.models._naziv import NazivQuerySet
from registar.utils.tekst import normalize_naziv


class Veroispovest(models.Model):
    """Класа која представља вероисповести."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(verbose_name="вероисповест", max_length=255)

    objects = NazivQuerySet.as_manager()

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
            models.UniqueConstraint(Lower("naziv"), name="veroispovest_naziv_ci_uniq"),
        ]
        db_table = "veroispovesti"
        verbose_name = "Вероисповест"
        verbose_name_plural = "Вероисповести"
