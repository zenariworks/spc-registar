"""
Model class for representing baptisms in the database.
"""
import uuid

from django.db import models

from .osoba import Osoba
from .svestenik import Svestenik


class Krstenje(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    datum_krstenja = models.DateTimeField()
    mesto_krstenja = models.CharField()
    krshram = models.CharField()

    aktgod = models.IntegerField()
    datum = models.DateField()
    mesto = models.CharField()
    proknj = models.CharField()
    protbr = models.IntegerField()
    protst = models.IntegerField()

    iz = models.CharField()
    ulica = models.CharField()
    broj = models.IntegerField()

    dete = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="дете")
    detmana = models.BooleanField()
    detimeg = models.CharField()
    detkoje = models.IntegerField()
    detbrac = models.BooleanField()
    blizanac = models.ForeignKey(
        Osoba, on_delete=models.CASCADE, related_name="близанац"
    )

    otac = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="отац")
    majka = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="мајка")

    svestenik = models.ForeignKey(
        Svestenik, on_delete=models.CASCADE, related_name="свештеник_крштени"
    )

    kum = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="кум")

    regmesto = models.TextField()
    regkada = models.TextField()
    regbroj = models.TextField()
    regstr = models.TextField()

    primedba = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштењe"
        verbose_name_plural = "Крштења"
