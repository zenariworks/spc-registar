"""Модул модела венчања у бази података."""

import uuid

from django.core.validators import MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from ._osoba_polja import (
    naziv_polja_osobe,
    opis_osobe,
    opis_veze,
    polje_osobe,
    popunjeno_polje_osobe,
)
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
        db_index=True,
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

    datum = models.DateField(verbose_name="датум", null=True, blank=True, db_index=True)

    zenik = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vencanja_kao_zenik",
        verbose_name="женик",
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

    history = HistoricalRecords(user_db_constraint=False)

    ime_zenika = polje_osobe("zenik", "ime", opis="Име женика.")
    prezime_zenika = polje_osobe("zenik", "prezime", opis="Презиме женика.")
    zanimanje_zenika = naziv_polja_osobe("zenik", "zanimanje", opis="Занимање женика.")
    veroispovest_zenika = popunjeno_polje_osobe(
        "zenik", "veroispovest", opis="Вероисповест женика."
    )
    narodnost_zenika = popunjeno_polje_osobe(
        "zenik", "narodnost", opis="Народност женика."
    )
    datum_rodjenja_zenika = polje_osobe(
        "zenik", "datum_rodjenja", prazno=None, opis="Датум рођења женика."
    )
    mesto_rodjenja_zenika = polje_osobe(
        "zenik", "mesto_rodjenja", opis="Место рођења женика."
    )
    adresa_zenika = polje_osobe("zenik", "adresa", prazno=None, opis="Адреса женика.")

    ime_neveste = polje_osobe("nevesta", "ime", opis="Име невесте.")
    prezime_neveste = popunjeno_polje_osobe(
        "nevesta", "devojacko", opis="Девојачко презиме невесте."
    )
    zanimanje_neveste = naziv_polja_osobe(
        "nevesta", "zanimanje", opis="Занимање невесте."
    )
    veroispovest_neveste = polje_osobe(
        "nevesta", "veroispovest", opis="Вероисповест невесте (None кад није уписана)."
    )
    narodnost_neveste = polje_osobe(
        "nevesta", "narodnost", opis="Народност невесте (None кад није уписана)."
    )
    datum_rodjenja_neveste = polje_osobe(
        "nevesta", "datum_rodjenja", prazno=None, opis="Датум рођења невесте."
    )
    mesto_rodjenja_neveste = polje_osobe(
        "nevesta", "mesto_rodjenja", opis="Место рођења невесте."
    )
    adresa_neveste = polje_osobe(
        "nevesta", "adresa", prazno=None, opis="Адреса невесте."
    )

    opis_svekra = opis_veze("svekar", opis="Отац женика (свекар).")
    opis_svekrve = opis_veze("svekrva", opis="Мајка женика (свекрва).")
    opis_tasta = opis_veze("tast", opis="Отац невесте (таст).")
    opis_taste = opis_veze("tasta", opis="Мајка невесте (ташта).")

    @property
    def opis_zenika(self):
        """Женик: име презиме, занимање, место становања, вера, народност."""
        return opis_osobe(
            self.ime_zenika,
            self.prezime_zenika,
            self.zanimanje_zenika,
            self.adresa_zenika,
            self.veroispovest_zenika,
            self.narodnost_zenika,
        )

    @property
    def opis_neveste(self):
        """Невеста: име, девојачко презиме, занимање, место, вера, народност."""
        return opis_osobe(
            self.ime_neveste,
            self.prezime_neveste,
            self.zanimanje_neveste,
            self.adresa_neveste,
            self.veroispovest_neveste,
            self.narodnost_neveste,
        )

    def __str__(self):
        z = self.ime_zenika or ""
        n = self.ime_neveste or ""
        if z or n:
            return f"Венчање {z} и {n} ({self.datum or ''})"
        return f"Венчање {self.uid}"

    class Meta:
        managed = True
        db_table = "vencanja"
        verbose_name = "Венчање"
        verbose_name_plural = "Венчања"
        ordering = ["-datum"]
        constraints = [
            # Протоколарни број је званична гаранција јединствености уписа:
            # у оквиру једне године регистрације редни број мора бити
            # јединствен. (knjiga, strana, broj) се намерно НЕ ограничава —
            # постојећи подаци садрже легитимна понављања физичке локације.
            models.UniqueConstraint(
                fields=["godina_registracije", "redni_broj"],
                name="vencanje_god_redni_uniq",
                violation_error_message=(
                    "Венчање са овим редним бројем у датој години "
                    "регистрације већ постоји."
                ),
            ),
        ]
        indexes = [
            models.Index(
                fields=["godina_registracije", "knjiga", "strana", "broj"],
                name="vencanje_protocol_idx",
            ),
        ]
