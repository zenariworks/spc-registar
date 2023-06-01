"""
Model class for representing sets in the database.
"""
from django.db import models


class Set(models.Model):
    hsp_godina = models.IntegerField()

    def __str__(self):
        return f"{self.hsp_godina}"

    class Meta:
        managed = True
        db_table = "sets"
