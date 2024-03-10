import uuid

from django.db import models


class Eparhija(models.Model):
    NIVO = [
        ("Епархија", "Епархија"),
        ("Архиепископија", "Архиепископија"),
        ("Митрополија", "Митрополија"),
    ]

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    nivo = models.CharField(
        max_length=15, choices=NIVO, default="Епархија", verbose_name="ниво"
    )
    naziv = models.CharField(max_length=100, verbose_name="назив")
    sediste = models.CharField(max_length=100, verbose_name="седиште")

    def __str__(self) -> str:
        return f"{self.nivo} - {self.naziv}"

    class Meta:
        managed = True
        db_table = "eparhije"
        verbose_name = "Епархија"
        verbose_name_plural = "Епархије"
