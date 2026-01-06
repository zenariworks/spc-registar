"""Модул модела венчања у бази података."""

import uuid

from django.core.validators import MinValueValidator
from django.db import models

from .base import TimestampedModel
from .hram import Hram
from .parohijan import Osoba
from .svestenik import Svestenik


class Vencanje(TimestampedModel):
    """Класа која представља венчања."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    zenik = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_zenik",
        verbose_name="женик",
    )
    nevesta = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_nevesta",
        verbose_name="невеста",
    )
    kum = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_kum",
        verbose_name="кум",
    )

    # tekuca godina i redni broj vencanja u godini
    redni_broj_vencanja_tekuca_godina = models.IntegerField(
        verbose_name="редни број венчања текућа година",
        validators=[MinValueValidator(1)],
    )
    vencanje_tekuca_godina = models.IntegerField(
        verbose_name="венчање текућа година",
        validators=[MinValueValidator(1900)],
    )

    # podaci za registar(protokol) vencanih
    knjiga = models.IntegerField(
        verbose_name="књига", validators=[MinValueValidator(1)]
    )
    strana = models.IntegerField(
        verbose_name="страна", validators=[MinValueValidator(1)]
    )
    tekuci_broj = models.IntegerField(
        verbose_name="текући број", validators=[MinValueValidator(1)]
    )

    datum = models.DateField(verbose_name="датум венчања", null=True, blank=True)

    # adrese (specifične za događaj venčanja)
    mesto_zenika = models.CharField(
        max_length=255, verbose_name="место женика", null=True, blank=True
    )
    adresa_zenika = models.CharField(
        max_length=255, verbose_name="адреса женика", null=True, blank=True
    )
    mesto_neveste = models.CharField(
        max_length=255, verbose_name="место невесте", null=True, blank=True
    )
    adresa_neveste = models.CharField(
        max_length=255, verbose_name="адреса невесте", null=True, blank=True
    )

    # podaci o roditeljima (ime oca/majke - nisu u Osoba modelu)
    svekar = models.CharField(max_length=255, verbose_name="име оца женика")
    svekrva = models.CharField(max_length=255, verbose_name="име мајке женика")
    tast = models.CharField(max_length=255, verbose_name="име оца невесте")
    tasta = models.CharField(max_length=255, verbose_name="име мајке невесте")

    # podaci o braku
    zenik_rb_brak = models.CharField(verbose_name="брак по реду женика")
    nevesta_rb_brak = models.CharField(verbose_name="брак по реду невесте")

    # podaci o ispitivanju
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

    stari_svat = models.CharField(
        max_length=255, verbose_name="име старог свата", null=True, blank=True
    )

    razresenje = models.CharField(verbose_name="разрешење")
    razresenje_primedba = models.TextField(verbose_name="примедба", blank=True)

    primedba = models.TextField(verbose_name="примедба", blank=True)

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "vencanja"
        verbose_name = "Венчање"
        verbose_name_plural = "Венчања"
