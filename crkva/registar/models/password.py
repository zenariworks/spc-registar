"""
Model class for representing passes in the database.
"""
import uuid

from django.db import models


class Password(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.IntegerField()
    naziv = models.TextField()
    nivo = models.IntegerField()
    flag = models.TextField()

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "passes"
        verbose_name = "Лозинка"
        verbose_name_plural = "Лозинке"
