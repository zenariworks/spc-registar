"""
Класа модела за представљање општине у бази података.
"""

import uuid

from django.db import models


class Opstina(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(max_length=100, verbose_name="назив")

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "opstine"
        verbose_name = "Општина"
        verbose_name_plural = "Општине"
