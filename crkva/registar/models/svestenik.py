"""Модул модела свештеника у бази података."""

import uuid

from django.db import models

from .parohija import Parohija

zvanja = [
    ("Патријарх Српски", "Патријарх Српски"),
    ("Јереј", "Јереј"),
    ("Протојереј", "Протојереј"),
    ("Протојереј-ставрофор", "Протојереј-ставрофор"),
    ("Протонамесник", "Протонамесник"),
    ("Администратор", "Администратор"),
    ("Митрополит", "Митрополит"),
]


class Svestenik(models.Model):
    """Класа која представља свештеника."""

    #uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    svestenik_id = models.IntegerField(verbose_name="свестеник ид", primary_key=True, unique=True)

    ime = models.CharField(verbose_name="име")
    prezime = models.CharField(verbose_name="презиме")

    mesto_rodjenja = models.CharField(verbose_name="место рођења")
    datum_rodjenja = models.DateField(blank=True, null=True, verbose_name="датум рођења")

    zvanje = models.CharField(max_length=30, choices=zvanja, verbose_name="звање")
    parohija = models.ForeignKey(
        Parohija,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="парохија",
    )

    def __str__(self) -> str:
        return f"{self.zvanje} {self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table: str = "svestenici"
        verbose_name: str = "Свештеник"
        verbose_name_plural: str = "Свештеници"
