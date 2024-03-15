"""
Класа модела за представљање улица у бази података.
"""

import uuid

from django.db import models

from .mesto import Mesto


class Ulica(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(max_length=255, verbose_name="назив")
    mesto = models.ForeignKey(Mesto, on_delete=models.CASCADE, verbose_name="место")
    svestenik = models.IntegerField(verbose_name="свештеник")

    def __str__(self):
        return f"{self.naziv}, {self.mesto}"

    class Meta:
        managed = True
        db_table = "ulice"
        verbose_name = "Улица"
        verbose_name_plural = "Улице"
