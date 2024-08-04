"""Модул модела државе у бази података."""

import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Drzava(models.Model):
    """Класа која представља државе."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(
        max_length=100, unique=True, blank=False, null=False, verbose_name="назив"
    )
    izvorni_naziv = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="изворни назив"
    )
    postkod_regex = models.CharField(
        max_length=128, blank=True, null=True, verbose_name="регекс поштанског броја"
    )

    def __str__(self):
        return self.naziv

    class Meta:
        managed = True
        db_table = "drzave"
        verbose_name = "Држава"
        verbose_name_plural = "Државе"

    def provera_postkoda(self, postkod):
        if self.postkod_regex and not re.match(self.postkod_regex, postkod):
            raise ValidationError("Поштански број не одговара формату државе.")
