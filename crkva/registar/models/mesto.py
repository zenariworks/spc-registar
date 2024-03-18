"""
Класа модела за представљање места у бази података.
"""

import uuid

from django.db import models


class Mesto(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(max_length=100, verbose_name="назив")

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "mesta"
        verbose_name = "Место"
        verbose_name_plural = "Места"
