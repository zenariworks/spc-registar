import uuid

from django.db import models

from .drzava import Drzava


class Opstina(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(max_length=100, verbose_name="назив")
    drzava = models.ForeignKey(Drzava, on_delete=models.CASCADE, verbose_name="држава")

    def __str__(self):
        return f"{self.naziv}, {self.drzava}"

    class Meta:
        managed = True
        db_table = "opstine"
        verbose_name = "Општина"
        verbose_name_plural = "Општине"
