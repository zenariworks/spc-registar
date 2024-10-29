"""Модул модела венчања у бази података."""

import uuid

from django.db import models

from .hram import Hram
from .svestenik import Svestenik


class Vencanje(models.Model):
    """Класа која представља венчања."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    # tekuca godina i redni broj vencanja u godini
    redni_broj_vencanja_tekuca_godina = models.IntegerField(
        verbose_name="редни број венчања текућа година"
    )
    vencanje_tekuca_godina = models.IntegerField(verbose_name="венчање текућа година")

    # podaci za registar(protokol) vencanih
    knjiga = models.IntegerField(verbose_name="књига")
    strana = models.IntegerField(verbose_name="страна")
    tekuci_broj = models.IntegerField(verbose_name="текући број")

    datum = models.DateField(verbose_name="датум венчања", null=True, blank=True)

    # podaci o zeniku
    ime_zenika = models.CharField(max_length=255, verbose_name="име женика")
    prezime_zenika = models.CharField(max_length=255, verbose_name="презиме женика")
    zanimanje_zenika = models.CharField(
        max_length=255, verbose_name="занимање женика", null=True, blank=True
    )
    mesto_zenika = models.CharField(
        max_length=255, verbose_name="место женика", null=True, blank=True
    )
    veroispovest_zenika = models.CharField(
        max_length=255, verbose_name="вероисповест женика", null=True, blank=True
    )
    narodnost_zenika = models.CharField(
        max_length=255, verbose_name="народност женика", null=True, blank=True
    )
    adresa_zenika = models.CharField(
        max_length=255, verbose_name="адреса женика", null=True, blank=True
    )

    # podaci o nevesti
    ime_neveste = models.CharField(max_length=255, verbose_name="име невесте")
    prezime_neveste = models.CharField(max_length=255, verbose_name="презиме невесте")
    zanimanje_neveste = models.CharField(
        max_length=255, verbose_name="занимање невесте", null=True, blank=True
    )
    mesto_neveste = models.CharField(
        max_length=255, verbose_name="место невесте", null=True, blank=True
    )
    veroispovest_neveste = models.CharField(
        max_length=255, verbose_name="вероисповест невесте", null=True, blank=True
    )
    narodnost_neveste = models.CharField(
        max_length=255, verbose_name="народност невесте", null=True, blank=True
    )
    adresa_neveste = models.CharField(
        max_length=255, verbose_name="адреса невесте", null=True, blank=True
    )

    # podaci o roditeljima
    svekar = models.CharField(max_length=255, verbose_name="име оца женика")
    svekrva = models.CharField(max_length=255, verbose_name="име мајке женика")
    tast = models.CharField(max_length=255, verbose_name="име оца невесте")
    tasta = models.CharField(max_length=255, verbose_name="име мајке невесте")

    # podaci o rodjenju zenika i neveste
    datum_rodjenja_zenika = models.DateField(verbose_name="датум рођења женика")
    mesto_rodjenja_zenika = models.CharField(
        max_length=255, verbose_name="место рођења женика", null=True, blank=True
    )
    datum_rodjenja_neveste = models.DateField(verbose_name="датум рођења невесте")
    mesto_rodjenja_neveste = models.CharField(
        max_length=255, verbose_name="место рођења невесте", null=True, blank=True
    )

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

    kum = models.CharField(
        max_length=255, verbose_name="име кума", null=True, blank=True
    )
    stari_svat = models.CharField(
        max_length=255, verbose_name="име старот свата", null=True, blank=True
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
