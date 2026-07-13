"""Модул модела свештеника у бази података."""

from django.conf import settings
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

    ime = models.CharField(verbose_name="име", max_length=100)
    prezime = models.CharField(verbose_name="презиме", max_length=100)

    mesto_rodjenja = models.CharField(
        verbose_name="место рођења", max_length=100, blank=True, null=True
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
        # No reverse accessor: frees the "svestenik" name on Adresa for the
        # street->priest FK added in #26 (this reverse was unused).
        related_name="+",
        verbose_name="адреса",
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="svestenik",
        # Cross-schema FK: User lives in the public schema; Postgres cannot
        # enforce FK constraints across schemas in django-tenants, so we drop
        # the DB-level constraint and keep only the Python-level relationship.
        db_constraint=False,
        verbose_name="кориснички налог",
        help_text=(
            "Налог којим се свештеник пријављује; потпис у подножју "
            "преписа (издавалац) узима свештеника везаног за "
            "пријављеног корисника."
        ),
    )

    history = HistoricalRecords(user_db_constraint=False)

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
