"""
Model class for representing residents in the database.
"""
from django.db import models


class Ukucanin(models.Model):
    uk_rbr = models.IntegerField()
    uk_rbrdom = models.IntegerField()
    uk_ime = models.TextField()
    uk_akt = models.TextField()
    uk_flag = models.TextField()

    def __str__(self):
        return f"{self.uk_rbr}"

    class Meta:
        managed = True
        db_table = "ukucani"
        verbose_name = "Укућанин"
        verbose_name_plural = "Укућани"
