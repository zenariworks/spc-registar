"""
Model class for representing baptisms in the database.
"""
from tabnanny import verbose
import uuid

from django.db import models

from .osoba import Osoba
from .svestenik import Svestenik


class Krstenje(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    knjiga = models.CharField(verbose_name="књига")
    strana = models.IntegerField(verbose_name="страна")
    tekuci_broj = models.IntegerField(verbose_name="текући број")

    datum = models.DateField(verbose_name="датум крштења")
    vreme = models.TimeField(verbose_name="време крштења")
    mesto = models.CharField(verbose_name="место крштења")
    hram = models.CharField(verbose_name="храм")

    aktgod = models.IntegerField()

    iz = models.CharField()
    ulica = models.CharField()
    broj = models.IntegerField()

    dete = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="дете")
    mana = models.BooleanField(verbose_name="мана")
    detimeg = models.CharField()
    dete_ = models.IntegerField(verbose_name="дете по реду (по мајци)")
    dete_bracno = models.BooleanField(verbose_name="брчно дете")
    blizanac = models.ForeignKey(
        Osoba, on_delete=models.CASCADE, related_name="близанац"
    )

    otac = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="отац")
    majka = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="мајка")

    svestenik = models.ForeignKey(Svestenik, on_delete=models.CASCADE, related_name="свештеник_крститељ")

    kum = models.ForeignKey(Osoba, on_delete=models.CASCADE, related_name="кум", verbose_name="кум")

    regmesto = models.TextField()
    regkada = models.TextField()
    regbroj = models.TextField()
    regstr = models.TextField()

    primedba = models.TextField(blank=True, null=True, verbose_name="примедба")

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "krstenja"
        verbose_name = "Крштењe"
        verbose_name_plural = "Крштења"
