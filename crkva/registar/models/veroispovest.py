"""
Model class for representing streets in the database.
"""
import uuid

from django.db import models


class Veroispovest(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(verbose_name="вероисповест", max_length=255)

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "veroispovests"
        verbose_name = "Вероисповест"
        verbose_name_plural = "Вероисповести"
