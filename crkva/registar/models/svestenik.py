"""Модул модела свештеника у бази података."""

from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

from .adresa import Adresa
from .parohija import Parohija

zvanja = [
    ("патријарх српски", "патријарх српски"),
    ("јереј", "јереј"),
    ("протојереј", "протојереј"),
    ("протојереј-ставрофор", "протојереј-ставрофор"),
    ("протонамесник", "протонамесник"),
    ("администратор", "администратор"),
    ("митрополит", "митрополит"),
]


class Svestenik(TimeStampedModel):
    """Класа која представља свештеника."""

    uid = models.AutoField(
        verbose_name="свестеник ид", primary_key=True, unique=True, editable=False
    )

    ime = models.CharField(verbose_name="име")
    prezime = models.CharField(verbose_name="презиме")

    mesto_rodjenja = models.CharField(
        verbose_name="место рођења", blank=True, null=True
    )
    datum_rodjenja = models.DateField(
        blank=True, null=True, verbose_name="датум рођења", default=None
    )

    zvanje = models.CharField(max_length=30, choices=zvanja, verbose_name="звање")
    parohija = models.ForeignKey(
        Parohija,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="парохија",
    )
    adresa = models.ForeignKey(
        Adresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="адреса",
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.zvanje} {self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table: str = "svestenici"
        verbose_name: str = "Свештеник"
        verbose_name_plural: str = "Свештеници"
        ordering = ["prezime", "ime"]
        indexes = [
            models.Index(fields=["created"], name="svestenik_created_idx"),
        ]
