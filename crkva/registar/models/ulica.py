"""
Model class for representing streets in the database.
"""
from django.db import models


class Ulica(models.Model):
    ul_rbr = models.IntegerField()
    ul_sifra = models.IntegerField()
    ul_naziv = models.TextField()
    ul_rbrsv = models.IntegerField()
    ul_akt = models.TextField()
    ul_flag = models.TextField()

    def __str__(self):
        return f"{self.ul_rbr}"

    class Meta:
        managed = True
        db_table = "ulice"
        verbose_name = "Улица"
        verbose_name_plural = "Улице"
