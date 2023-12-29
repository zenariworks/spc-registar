import uuid

from django.db import models

from .eparhija import Eparhija


class CrkvenaOpstina(models.Model):
    naziv = models.CharField(max_length=100, verbose_name="назив")
    eparhija = models.ForeignKey(Eparhija, on_delete=models.CASCADE, verbose_name="епархија")

    def __str__(self):
        return self.naziv

    class Meta:
        managed = True
        db_table = "crkvene_opstine"
        verbose_name = "Црквена општина"
        verbose_name_plural = "Црквене општине"
    