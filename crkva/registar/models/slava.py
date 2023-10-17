"""
Model class for representing slavas in the database.
"""
import uuid

from django.db import models

from .dan import Dan
from .mesec import Mesec


class Slava(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.IntegerField(name="шифра")
    naziv = models.CharField(name="назив")
    dan = models.ForeignKey(Dan, on_delete=models.CASCADE, name="дан")
    mesec = models.ForeignKey(Mesec, on_delete=models.CASCADE, name="месец")
    akt = models.CharField(name="акт")
    flag = models.CharField(name="флаг")

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "славе"
        verbose_name = "Слава"
        verbose_name_plural = "Славе"
