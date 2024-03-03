"""
Model class for representing weddings in the database.
"""
import uuid

from django.db import models

from .hram import Hram
from .parohijan import Parohijan
from .svestenik import Svestenik


class Vencanje(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    knjiga = models.IntegerField(verbose_name="књига")
    strana = models.IntegerField(verbose_name="страна")
    tekuci_broj = models.IntegerField(verbose_name="текући број")

    datum = models.DateField(verbose_name="датум венчања")

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
    datum_ispita = models.DateField(verbose_name="датум испита")

    hram = models.ForeignKey(
        Hram, on_delete=models.SET_NULL, null=True, verbose_name="место венчања"
    )
    svestenik = models.ForeignKey(
        Svestenik,
        verbose_name="свештеник",
        on_delete=models.SET_NULL,
        null=True,
        related_name="свештеник_венчани",
    )
    parohija = models.CharField(verbose_name="свешт. парохија")

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

    napomena = models.TextField(verbose_name="напомена")

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "vencanja"
        verbose_name = "Венчање"
        verbose_name_plural = "Венчања"
