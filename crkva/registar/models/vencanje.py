"""Модул модела венчања у бази података."""

import uuid

from django.core.validators import MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from .hram import Hram
from .parohijan import Osoba
from .svestenik import Svestenik


class Vencanje(TimeStampedModel):  # pylint: disable=too-many-public-methods
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

    history = HistoricalRecords()

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
        return (
            str(self.zenik.zanimanje) if self.zenik and self.zenik.zanimanje_id else ""
        )

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
        return (
            str(self.nevesta.zanimanje)
            if self.nevesta and self.nevesta.zanimanje_id
            else ""
        )

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

    @property
    def adresa_zenika(self):
        """Адреса женика из везаног Osoba objekta."""
        return self.zenik.adresa if self.zenik else None

    @property
    def adresa_neveste(self):
        """Адреса невесте из везаног Osoba objekta."""
        return self.nevesta.adresa if self.nevesta else None

    @staticmethod
    def _spoji(*delovi):
        """Спаја непразне делове зарезом (без празнина и двоструких зареза)."""
        return ", ".join(
            str(d).strip() for d in delovi if d is not None and str(d).strip()
        )

    @staticmethod
    def _mala(vrednost):
        """Мала слова за заједничке именице (вера, народност)."""
        return str(vrednost).lower() if vrednost else ""

    @staticmethod
    def _opis_osobe(osoba):
        """Родитељ (особа) у реду: име презиме, занимање, место становања."""
        if not osoba:
            return ""
        ime = " ".join(p for p in (osoba.ime, osoba.prezime) if p)
        zanimanje = Vencanje._mala(osoba.zanimanje)
        mesto = osoba.adresa.mesto if osoba.adresa_id and osoba.adresa else ""
        return Vencanje._spoji(ime, zanimanje, mesto)

    @property
    def opis_zenika(self):
        """Женик: име презиме, занимање, место становања, вера, народност."""
        ime = " ".join(p for p in (self.ime_zenika, self.prezime_zenika) if p)
        mesto = self.adresa_zenika.mesto if self.adresa_zenika else ""
        return self._spoji(
            ime, self._mala(self.zanimanje_zenika), mesto,
            self._mala(self.veroispovest_zenika), self._mala(self.narodnost_zenika),
        )

    @property
    def opis_neveste(self):
        """Невеста: име презиме, занимање, место становања, вера, народност."""
        ime = " ".join(p for p in (self.ime_neveste, self.prezime_neveste) if p)
        mesto = self.adresa_neveste.mesto if self.adresa_neveste else ""
        return self._spoji(
            ime, self._mala(self.zanimanje_neveste), mesto,
            self._mala(self.veroispovest_neveste), self._mala(self.narodnost_neveste),
        )

    @property
    def opis_svekra(self):
        """Отац женика (свекар)."""
        return self._opis_osobe(self.svekar)

    @property
    def opis_svekrve(self):
        """Мајка женика (свекрва)."""
        return self._opis_osobe(self.svekrva)

    @property
    def opis_tasta(self):
        """Отац невесте (таст)."""
        return self._opis_osobe(self.tast)

    @property
    def opis_taste(self):
        """Мајка невесте (ташта)."""
        return self._opis_osobe(self.tasta)

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
