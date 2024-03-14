"""
Класа модела за представљање свштеника у бази података.
"""

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
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    ime = models.CharField(verbose_name="име")
    prezime = models.CharField(verbose_name="презиме")

    mesto_rodjenja = models.CharField(verbose_name="место рођења")
    datum_rodjenja = models.DateField(verbose_name="датум рођења")

    zvanje = models.CharField(max_length=30, choices=zvanja, verbose_name="звање")
    parohija = models.ForeignKey(
        Parohija,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="парохија",
    )

    def __str__(self) -> str:
        return f"{self.zvanje}, {self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table: str = "svestenici"
        verbose_name: str = "Свештеник"
        verbose_name_plural: str = "Свештеници"
