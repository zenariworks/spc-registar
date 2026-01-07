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

    godina_registracije = models.IntegerField(
        verbose_name="година регистрације",
        validators=[MinValueValidator(1900)],
        default=2000,
    )
    redni_broj = models.IntegerField(
        verbose_name="редни број венчања",
        validators=[MinValueValidator(1)],
        default=1,
    )

    knjiga = models.IntegerField(
        verbose_name="књига", validators=[MinValueValidator(1)], default=1
    )
    strana = models.IntegerField(
        verbose_name="страна", validators=[MinValueValidator(1)], default=1
    )
    tekuci_broj = models.IntegerField(
        verbose_name="текући број", validators=[MinValueValidator(1)], default=1
    )

    datum = models.DateField(verbose_name="датум венчања", null=True, blank=True)

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

    # podaci o braku
    zenik_rb_brak = models.PositiveSmallIntegerField(
        verbose_name="брак по реду женика", validators=[MinValueValidator(1)], default=1
    )
    nevesta_rb_brak = models.PositiveSmallIntegerField(
        verbose_name="брак по реду невесте",
        validators=[MinValueValidator(1)],
        default=1,
    )

    svekar = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_svekar",
        verbose_name="отац женика",
    )
    svekrva = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_svekrva",
        verbose_name="мајка женика",
    )
    tast = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_tast",
        verbose_name="отац невесте",
    )
    tasta = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_tasta",
        verbose_name="мајка невесте",
    )

    stari_svat = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_stari_svat",
        verbose_name="име старог свата",
    )

    datum_ispita = models.DateField(
        verbose_name="датум испита",
        validators=[MinValueValidator(1900)],
        null=True,
        blank=True,
    )

    hram = models.ForeignKey(
        Hram,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="место венчања",
    )
    svestenik = models.ForeignKey(
        Svestenik,
        verbose_name="свештеник",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="свештеник_венчани",
    )

    razresenje = models.BooleanField(verbose_name="разрешење", default=True)
    primedba = models.TextField(verbose_name="примедба", blank=True, default="")

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "vencanja"
        verbose_name = "Венчање"
        verbose_name_plural = "Венчања"
