"""Модул модела парохијана у бази података."""

import uuid

from django.db import models

from .adresa import Adresa
from .narodnost import Narodnost
from .veroispovest import Veroispovest
from .zanimanje import Zanimanje


class Parohijan(models.Model):
    """Класа која представља парохијана."""

    uid = models.IntegerField(primary_key=True, unique=True, editable=False)

    ime = models.CharField(verbose_name="име")
    prezime = models.CharField(verbose_name="презиме")
    mesto_rodjenja = models.CharField(verbose_name="место рођења")
    # blank=True, null=True, - field is optional
    datum_rodjenja = models.DateField(verbose_name="датум рођења", blank=True, null=True)
    vreme_rodjenja = models.TimeField(verbose_name="време рођења", blank=True, null=True)
    pol = models.CharField(
        verbose_name="пол", choices=[("М", "мушки"), ("Ж", "женски")]
    )

    devojacko_prezime = models.CharField(verbose_name="девојачко презиме", blank=True)
    
    # replace the following foreign keys with a custom char field
    #zanimanje = models.CharField(verbose_name="занимање", blank=True, null=True)
    #veroispovest = models.CharField(verbose_name="вероисповест", blank=True, null=True)
    #narodnost = models.CharField(verbose_name="народност", blank=True, null=True)
    
    zanimanje = models.ForeignKey(
        Zanimanje,
        verbose_name="занимање",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    veroispovest = models.ForeignKey(
        Veroispovest,
        verbose_name="вероисповест",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    narodnost = models.ForeignKey(
        Narodnost,
        verbose_name="народност",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    adresa = models.ForeignKey(
        Adresa, on_delete=models.SET_NULL, null=True, verbose_name="адреса"
    )

    def __str__(self):
        return f"{self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table = "parohijani"
        verbose_name = "Парохијан"
        verbose_name_plural = "Парохијани"
