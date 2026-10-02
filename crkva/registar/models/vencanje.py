"""Модул модела венчања у бази података."""

import uuid

from django.core.validators import MinValueValidator
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from ._osoba_polja import naziv_polja_osobe, polje_osobe, popunjeno_polje_osobe
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
            ime,
            self._mala(self.zanimanje_zenika),
            mesto,
            self._mala(self.veroispovest_zenika),
            self._mala(self.narodnost_zenika),
        )

    @property
    def opis_neveste(self):
        """Невеста: име презиме, занимање, место становања, вера, народност."""
        ime = " ".join(p for p in (self.ime_neveste, self.prezime_neveste) if p)
        mesto = self.adresa_neveste.mesto if self.adresa_neveste else ""
        return self._spoji(
            ime,
            self._mala(self.zanimanje_neveste),
            mesto,
            self._mala(self.veroispovest_neveste),
            self._mala(self.narodnost_neveste),
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
