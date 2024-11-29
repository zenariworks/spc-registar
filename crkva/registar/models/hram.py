"""Модул модела храма у бази података."""

import uuid

from django.db import models


class Hram(models.Model):
    """Класа која представља храмове."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=200, verbose_name="назив")

    def __str__(self):
        return self.naziv

    class Meta:
        managed = True
        db_table = "hramovi"
        verbose_name = "Храм"
        verbose_name_plural = "Храмови"
