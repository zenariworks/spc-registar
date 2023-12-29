"""
Model class for representing priests in the database.
"""
import uuid

from django.db import models

from .osoba import Osoba


class Svestenik(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    zvanje = models.CharField(verbose_name="звање")
    parohija = models.CharField(verbose_name="парохија")
    osoba = models.ForeignKey(Osoba, verbose_name="особа", on_delete=models.CASCADE, related_name="свештеник")

    def __str__(self):
        return f"{self.zvanje}, {self.osoba.ime} {self.osoba.prezime}"

    class Meta:
        managed = True
        db_table = "svestenici"
        verbose_name = "Свештеник"
        verbose_name_plural = "Свештеници"
