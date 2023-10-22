"""
Model class for representing residents in the database.
"""
import uuid

from django.db import models
from registar.models import Domacinstvo


class Ukucanin(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    rbrdom = models.IntegerField()

    ime = models.CharField()

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "ukucani"
        verbose_name = "Укућанин"
        verbose_name_plural = "Укућани"
