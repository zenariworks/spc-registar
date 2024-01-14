"""
Model class for representing weddings in the database.
"""
import uuid

from django.db import models

from .dan import Dan
from .mesec import Mesec
from .parohijan import Parohijan
from .svestenik import Svestenik


class Vencanje(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    datum = models.DateField(verbose_name="датум")
    godina = models.IntegerField(verbose_name="година")
    mesec = models.ForeignKey(
        Mesec, verbose_name="месец", on_delete=models.SET_NULL, null=True
    )
    dan = models.ForeignKey(
        Dan, verbose_name="дан", on_delete=models.SET_NULL, null=True
    )

    knjiga = models.IntegerField(verbose_name="књига")
    strana = models.IntegerField(verbose_name="страна")
    tekuci_broj = models.IntegerField(verbose_name="текући број")

    zenik = models.ForeignKey(
        Parohijan,
        verbose_name="женик",
        on_delete=models.SET_NULL,
        null=True,
        related_name="женик",
    )
    zenik_rb_brak = models.IntegerField(verbose_name="Рб. брак женика")

    nevesta = models.ForeignKey(
        Parohijan,
        verbose_name="невеста",
        on_delete=models.SET_NULL,
        null=True,
        related_name="невеста",
    )
    nevesta_rb_brak = models.IntegerField(verbose_name="Рб. брак невесте")

    tast = models.ForeignKey(
        Parohijan,
        verbose_name="таст",
        on_delete=models.SET_NULL,
        null=True,
        related_name="таст",
    )
    tasta = models.ForeignKey(
        Parohijan,
        verbose_name="ташта",
        on_delete=models.SET_NULL,
        null=True,
        related_name="ташта",
    )

    svekar = models.ForeignKey(
        Parohijan,
        verbose_name="свекар",
        on_delete=models.SET_NULL,
        null=True,
        related_name="свекар",
    )
    svekrva = models.ForeignKey(
        Parohijan,
        verbose_name="свекрва",
        on_delete=models.SET_NULL,
        null=True,
        related_name="свекрва",
    )

    ispitgod = models.IntegerField(verbose_name="испит година")
    ispitmes = models.IntegerField(verbose_name="испит место")
    ispitdan = models.IntegerField(verbose_name="испит књига")

    hram_ime = models.CharField(verbose_name="назив храма")
    hram_mesto = models.CharField(verbose_name="место храма")
    svestenik = models.ForeignKey(
        Svestenik,
        verbose_name="свештеник",
        on_delete=models.SET_NULL,
        null=True,
        related_name="свештеник_венчани",
    )
    svestenik_par = models.CharField(verbose_name="свешт. парохија")

    kum = models.ForeignKey(
        Parohijan,
        verbose_name="кум",
        on_delete=models.SET_NULL,
        null=True,
        related_name="венчани_кум",
    )
    kuma = models.ForeignKey(
        Parohijan,
        verbose_name="кума",
        on_delete=models.SET_NULL,
        null=True,
        related_name="венчана_кума",
    )

    srazrdn = models.BooleanField(verbose_name="нешто нешто")
    napomena = models.TextField(verbose_name="напомена")

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "vencanja"
        verbose_name = "Венчање"
        verbose_name_plural = "Венчања"
