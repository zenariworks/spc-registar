"""Модул модела дана у бази података."""

from django.db import models


class Dan(models.Model):
    """Класа која представља дане."""

    dan = models.IntegerField(verbose_name="дан", primary_key=True, unique=True)

    def __str__(self):
        return f"{self.dan}"

    class Meta:
        managed = True
        db_table = "dani"
        verbose_name = "Дан"
        verbose_name_plural = "Дани"
