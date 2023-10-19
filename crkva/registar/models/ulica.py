"""
Model class for representing streets in the database.
"""
import uuid

from django.db import models


class Ulica(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(verbose_name="назив", max_length=255)
    svestenik = models.IntegerField(verbose_name="свештеник")

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "ulice"
        verbose_name = "Улица"
        verbose_name_plural = "Улице"
