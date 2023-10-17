"""
Model class for representing slavas in the database.
"""
from django.db import models


class Mesec(models.Model):
    mesec = models.IntegerField(primary_key=True, unique=True, name="месец")
    naziv = models.CharField(max_length=10, verbose_name="назив")

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "месеци"
        verbose_name = "Месец"
        verbose_name_plural = "Месеци"
