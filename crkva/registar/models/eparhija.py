import uuid
from django.db import models


class Eparhija(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=100, verbose_name="назив")
    sediste = models.CharField(max_length=100, verbose_name="седиште")

    def __str__(self) -> str:
        return self.naziv

    class Meta:
        managed = True
        db_table: str = "eparhije"
        verbose_name: str = "Епархија"
        verbose_name_plural: str = "Епархије"
