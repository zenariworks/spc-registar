"""
Model class for representing baptisms in the database.
"""
import uuid

from django.db import models

from .hram import Hram
from .osoba import Osoba
from .svestenik import Svestenik


class Krstenje(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    knjiga = models.IntegerField(verbose_name="протоколарна књига")
    strana = models.IntegerField(verbose_name="протоколарна страна")
    tekuci_broj = models.IntegerField(verbose_name="протоколарни број")

    datum = models.DateField(verbose_name="датум крштења")
    vreme = models.TimeField(verbose_name="време крштења")
    hram = models.ForeignKey(Hram, on_delete=models.CASCADE, verbose_name="место крштења")

    dete = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="дете", verbose_name="дете")
    dete_majci = models.IntegerField(verbose_name="дете по реду (по мајци)")
    dete_bracno = models.BooleanField(verbose_name="брачно дете")
    mana = models.BooleanField(verbose_name="мана")
    blizanac = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="близанац", verbose_name="близанац")
    
    detimeg = models.TextField() # ???

    otac = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="отац", verbose_name="отац")
    majka = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="мајка", verbose_name="мајка")
    svestenik = models.ForeignKey(Svestenik, on_delete=models.CASCADE, related_name="свештеник_крститељ", verbose_name="свештеник")
    kum = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="кум", verbose_name="кум")

    primedba = models.TextField(blank=True, null=True, verbose_name="примедба")

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштењe"
        verbose_name_plural = "Крштења"
