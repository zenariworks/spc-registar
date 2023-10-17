"""
Model class for representing baptisms in the database.
"""
import uuid

from django.db import models


class Krstenje(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.IntegerField()
    aktgod = models.IntegerField()
    datum = models.DateField()
    mesto = models.CharField()
    proknj = models.CharField()
    protbr = models.IntegerField()
    protst = models.IntegerField()
    iz = models.CharField()
    ulica = models.CharField()
    broj = models.IntegerField()
    rodjgod = models.IntegerField()
    rodjmese = models.IntegerField()
    rodjdan = models.IntegerField()
    rodjvre = models.TextField()
    rodjmest = models.TextField()
    rodjopst = models.TextField()
    krsgod = models.IntegerField()
    krsmese = models.IntegerField()
    krsdan = models.IntegerField()
    krsvre = models.TextField()
    krsmest = models.CharField()
    krshram = models.CharField()
    detime = models.CharField()
    detimeg = models.TextField()
    detpol = models.CharField()
    rodime = models.TextField()
    rodprez = models.TextField()
    rodzanim = models.CharField()
    rodmest = models.TextField()
    rodvera = models.TextField()
    rodnarod = models.TextField()
    rod2ime = models.TextField()
    rod2prez = models.TextField()
    rod2zan = models.TextField()
    rod2mest = models.TextField()
    rod2vera = models.TextField()
    detzivo = models.TextField()
    detkoje = models.IntegerField()
    detbrac = models.TextField()
    detbliz = models.TextField()
    detbliz2 = models.TextField()
    detmana = models.TextField()
    rbrsve = models.IntegerField()
    sveime = models.TextField()
    svezva = models.TextField()
    svepar = models.TextField()
    kumime = models.TextField()
    kumprez = models.TextField()
    kumzanim = models.TextField()
    kummest = models.TextField()
    regmesto = models.TextField()
    regkada = models.TextField()
    regbroj = models.TextField()
    regstr = models.TextField()

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштењe"
        verbose_name_plural = "Крштења"
