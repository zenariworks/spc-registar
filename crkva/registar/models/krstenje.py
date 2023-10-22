"""
Model class for representing baptisms in the database.
"""
import uuid

from django.db import models

from .osoba import Osoba
from .svestenik import Svestenik


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
    krsgod = models.IntegerField()
    krsmese = models.IntegerField()
    krsdan = models.IntegerField()
    krsvre = models.TextField()
    krsmest = models.CharField()
    krshram = models.CharField()

    dete = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="дете")

    detimeg = models.TextField()
    rodjopst = models.TextField()

    otac = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="отац")
    majka = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="мајка")

    detzivo = models.TextField()
    detkoje = models.IntegerField()
    detbrac = models.TextField()
    detbliz = models.TextField()
    detbliz2 = models.TextField()
    detmana = models.TextField()
    rbrsve = models.IntegerField()

    svestenik = models.ForeignKey(Svestenik, on_delete=models.CASCADE, related_name="свештеник")
    
    kum = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="кум")

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
