"""Модул модела месеца у бази података."""

from django.db import models


class Mesec(models.Model):
    """Класа која представља месеце."""

    mesec = models.IntegerField(verbose_name="месец", primary_key=True, unique=True)
    naziv = models.CharField(verbose_name="назив", max_length=10)

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "meseci"
        verbose_name = "Месец"
        verbose_name_plural = "Месеци"
