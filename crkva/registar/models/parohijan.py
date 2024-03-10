"""
Model class for representing sets in the database.
"""
import uuid

from django.db import models

from .adresa import Adresa
from .narodnost import Narodnost
from .veroispovest import Veroispovest
from .zanimanje import Zanimanje


class Parohijan(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    ime = models.CharField(verbose_name="име")
    prezime = models.CharField(verbose_name="презиме")
    mesto_rodjenja = models.CharField(verbose_name="место рођења")
    datum_rodjenja = models.DateField(verbose_name="датум рођења")
    vreme_rodjenja = models.TimeField(verbose_name="време рођења", blank=True)
    pol = models.CharField(
        verbose_name="пол", choices=[("М", "мушки"), ("Ж", "женски")]
    )

    devojacko_prezime = models.CharField(verbose_name="девојачко презиме", blank=True)
    zanimanje = models.ForeignKey(
        Zanimanje,
        verbose_name="занимање",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    veroispovest = models.ForeignKey(
        Veroispovest,
        verbose_name="вероисповест",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    narodnost = models.ForeignKey(
        Narodnost,
        verbose_name="народност",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    adresa = models.ForeignKey(
        Adresa, on_delete=models.SET_NULL, null=True, verbose_name="адреса"
    )

    def __str__(self):
        return f"{self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table = "parohijani"
        verbose_name = "Парохијан"
        verbose_name_plural = "Парохијани"
