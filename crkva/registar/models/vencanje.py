"""Модул модела венчања у бази података."""

import uuid

from django.core.validators import MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel

from .hram import Hram
from .parohijan import Osoba
from .svestenik import Svestenik


class Vencanje(TimeStampedModel):
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
    broj = models.IntegerField(
        verbose_name="текући број", validators=[MinValueValidator(1)], default=1
    )

    datum = models.DateField(verbose_name="датум", null=True, blank=True)

    zenik = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_zenik",
        verbose_name="женик",
    )
    # adrese (specifične za događaj venčanja)
    mesto_zenika = models.CharField(
        max_length=255, verbose_name="место женика", null=True, blank=True
    )
    adresa_zenika = models.CharField(
        max_length=255, verbose_name="адреса женика", null=True, blank=True
    )
    zenik_rb_brak = models.PositiveSmallIntegerField(
        verbose_name="брак по реду женика", validators=[MinValueValidator(1)], default=1
    )

    nevesta = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_nevesta",
        verbose_name="невеста",
    )
    mesto_neveste = models.CharField(
        max_length=255, verbose_name="место невесте", null=True, blank=True
    )
    adresa_neveste = models.CharField(
        max_length=255, verbose_name="адреса невесте", null=True, blank=True
    )
    nevesta_rb_brak = models.PositiveSmallIntegerField(
        verbose_name="брак по реду невесте",
        validators=[MinValueValidator(1)],
        default=1,
    )

    kum = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_kum",
        verbose_name="кум",
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

    @property
    def ime_zenika(self):
        """Име женика из везаног Osoba objekta."""
        return self.zenik.ime if self.zenik else ""

    @property
    def prezime_zenika(self):
        """Презиме женика из везаног Osoba objekta."""
        return self.zenik.prezime if self.zenik else ""

    @property
    def zanimanje_zenika(self):
        """Занимање женика из везаног Osoba objekta."""
        return self.zenik.zanimanje if self.zenik and self.zenik.zanimanje else ""

    @property
    def veroispovest_zenika(self):
        """Вероисповест женика из везаног Osoba objekta."""
        return self.zenik.veroispovest if self.zenik and self.zenik.veroispovest else ""

    @property
    def narodnost_zenika(self):
        """Народност женика из везаног Osoba objekta."""
        return self.zenik.narodnost if self.zenik and self.zenik.narodnost else ""

    @property
    def datum_rodjenja_zenika(self):
        """Датум рођења женика из везаног Osoba objekta."""
        return self.zenik.datum_rodjenja if self.zenik else None

    @property
    def mesto_rodjenja_zenika(self):
        """Место рођења женика из везаног Osoba objekta."""
        return self.zenik.mesto_rodjenja if self.zenik else ""

    @property
    def ime_neveste(self):
        """Име невесте из везаног Osoba objekta."""
        return self.nevesta.ime if self.nevesta else ""

    @property
    def prezime_neveste(self):
        """Девојачко презиме невесте из везаног Osoba objekta."""
        return (
            self.nevesta.devojacko_prezime
            if self.nevesta and self.nevesta.devojacko_prezime
            else ""
        )

    @property
    def zanimanje_neveste(self):
        """Занимање невесте из везаног Osoba objekta."""
        return self.nevesta.zanimanje if self.nevesta else ""

    @property
    def veroispovest_neveste(self):
        """Вероисповест невесте из везаног Osoba objekta."""
        return self.nevesta.veroispovest if self.nevesta else ""

    @property
    def narodnost_neveste(self):
        """Народност невесте из везаног Osoba objekta."""
        return self.nevesta.narodnost if self.nevesta else ""

    @property
    def datum_rodjenja_neveste(self):
        """Датум рођења невесте из везаног Osoba objekta."""
        return self.nevesta.datum_rodjenja if self.nevesta else None

    @property
    def mesto_rodjenja_neveste(self):
        """Место рођења невесте из везаног Osoba objekta."""
        return self.nevesta.mesto_rodjenja if self.nevesta else ""

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "vencanja"
        verbose_name = "Венчање"
        verbose_name_plural = "Венчања"
