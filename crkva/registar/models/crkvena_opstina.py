import uuid

from django.db import models

from .eparhija import Eparhija


class CrkvenaOpstina(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=100, verbose_name="назив")
    eparhija = models.ForeignKey(
        Eparhija, on_delete=models.SET_NULL, null=True, verbose_name="епархија"
    )

    def __str__(self) -> str:
        return f"{self.naziv}, {self.eparhija.naziv}"

    class Meta:
        managed = True
        db_table: str = "crkvene_opstine"
        verbose_name: str = "Црквена општина"
        verbose_name_plural: str = "Црквене општине"
