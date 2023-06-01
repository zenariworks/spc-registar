"""
Model class for representing priests in the database.
"""
from django.db import models


class Svestenik(models.Model):
    sv_rbr = models.IntegerField()
    sv_sifra = models.IntegerField()
    sv_ime = models.TextField()
    sv_zvanje = models.TextField()
    sv_paroh = models.TextField()
    sv_datrod = models.TextField()
    sv_akt = models.TextField()
    sv_flag = models.TextField()

    def __str__(self):
        return f"{self.sv_rbr}"

    class Meta:
        managed = True
        db_table = "svestenici"
