"""
Model class for representing priests in the database.
"""
import uuid

from django.db import models


class Svestenik(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.IntegerField()
    ime = models.CharField()
    zvanje = models.CharField()
    paroh = models.CharField()
    datrod = models.DateField()
    akt = models.CharField()
    flag = models.CharField()

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "svestenici"
        verbose_name = "Свештеник"
        verbose_name_plural = "Свештеници"
