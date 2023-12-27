import uuid

from django.db import models

from .adresa import Adresa


class Hram(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=200)
    adresa = models.ForeignKey(Adresa, on_delete=models.CASCADE)

    def __str__(self):
        return self.naziv

    class Meta:
        managed = True
        db_table = "hramovi"
        verbose_name = "Храм"
        verbose_name_plural = "Храмови"
