"""
Model class for representing baptisms in the database.
"""
from django.db import models


class Krstenje(models.Model):
    k_rbr = models.IntegerField()
    k_sifra = models.IntegerField()
    k_aktgod = models.IntegerField()
    k_datum = models.TextField()
    k_mesto = models.TextField()
    k_proknj = models.TextField()
    k_protbr = models.TextField()
    k_protst = models.IntegerField()
    k_iz = models.TextField()
    k_ulica = models.TextField()
    k_broj = models.TextField()
    k_rodjgod = models.IntegerField()
    k_rodjmese = models.IntegerField()
    k_rodjdan = models.IntegerField()
    k_rodjvre = models.TextField()
    k_rodjmest = models.TextField()
    k_rodjopst = models.TextField()
    k_krsgod = models.IntegerField()
    k_krsmese = models.IntegerField()
    k_krsdan = models.IntegerField()
    k_krsvre = models.TextField()
    k_krsmest = models.TextField()
    k_krshram = models.TextField()
    k_detime = models.TextField()
    k_detimeg = models.TextField()
    k_detpol = models.TextField()
    k_rodime = models.TextField()
    k_rodprez = models.TextField()
    k_rodzanim = models.TextField()
    k_rodmest = models.TextField()
    k_rodvera = models.TextField()
    k_rodnarod = models.TextField()
    k_rod2ime = models.TextField()
    k_rod2prez = models.TextField()
    k_rod2zan = models.TextField()
    k_rod2mest = models.TextField()
    k_rod2vera = models.TextField()
    k_detzivo = models.TextField()
    k_detkoje = models.IntegerField()
    k_detbrac = models.TextField()
    k_detbliz = models.TextField()
    k_detbliz2 = models.TextField()
    k_detmana = models.TextField()
    k_rbrsve = models.IntegerField()
    k_sveime = models.TextField()
    k_svezva = models.TextField()
    k_svepar = models.TextField()
    k_kumime = models.TextField()
    k_kumprez = models.TextField()
    k_kumzanim = models.TextField()
    k_kummest = models.TextField()
    k_regmesto = models.TextField()
    k_regkada = models.TextField()
    k_regbroj = models.TextField()
    k_regstr = models.TextField()

    def __str__(self):
        return f"{self.k_rbr}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштењe"
        verbose_name_plural = "Крштења"
