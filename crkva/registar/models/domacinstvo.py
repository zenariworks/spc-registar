"""
Model class for representing households in the database.
"""
from django.db import models


class Domacinstvo(models.Model):
    dom_rbr = models.IntegerField()
    dom_sifra = models.IntegerField()
    dom_ime = models.TextField()
    dom_ukuc = models.TextField()
    dom_rbrul = models.IntegerField()
    dom_ulbroj = models.TextField()
    dom_broj = models.IntegerField()
    dom_oznaka = models.TextField()
    dom_stan = models.TextField()
    dom_teldir = models.TextField()
    dom_telmob = models.TextField()
    dom_rbrsl = models.IntegerField()
    dom_slavod = models.TextField()
    dom_uskvod = models.TextField()
    dom_napom = models.TextField()
    dom_akt = models.TextField()
    dom_flag = models.TextField()

    def __str__(self):
        return f"{self.dom_rbr}"

    class Meta:
        managed = True
        db_table = "domacinstva"
