"""
Model class for representing streets in the database.
"""
import uuid

from django.db import models


class Ulica(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.IntegerField()
    naziv = models.CharField()
    svestenik = models.IntegerField()
    akt = models.TextField()
    flag = models.TextField()

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "ulice"
        verbose_name = "Улица"
        verbose_name_plural = "Улице"
