"""Модул модела парохијана у бази података."""

from django.db import models

from .adresa import Adresa
from .slava import Slava


class Parohijan(models.Model):
    """Класа која представља парохијана."""
    uid = models.IntegerField(primary_key=True, unique=True, editable=False)

    ime = models.CharField(verbose_name="име")
    prezime = models.CharField(verbose_name="презиме")

    adresa = models.ForeignKey(
        Adresa, on_delete=models.SET_NULL, null=True, verbose_name="адреса"
    )

    slava = models.ForeignKey(Slava, on_delete=models.SET_NULL, null=True, verbose_name="слава")
    tel_fiksni = models.CharField(verbose_name="фиксни телефон", blank=True, null=True)
    tel_mobilni = models.CharField(verbose_name="мобилни телефон", blank=True, null=True)
    slavska_vodica = models.BooleanField(default=False, verbose_name="славска водица")
    uskrsnja_vodica = models.BooleanField(default=False, verbose_name="ускршња водица")

    mesto_rodjenja = models.CharField(verbose_name="место рођења", blank=True, null=True)
    datum_rodjenja = models.DateField(verbose_name="датум рођења", blank=True, null=True)
    vreme_rodjenja = models.TimeField(verbose_name="време рођења", blank=True, null=True)
    pol = models.CharField(
        verbose_name="пол", choices=[("М", "мушки"), ("Ж", "женски")], blank=True, null=True
    )

    devojacko_prezime = models.CharField(verbose_name="девојачко презиме", blank=True, null=True)
    
    zanimanje = models.CharField(verbose_name="занимање", blank=True, null=True)
    veroispovest = models.CharField(verbose_name="вероисповест", blank=True, null=True)
    narodnost = models.CharField(verbose_name="народност", blank=True, null=True)

    def __str__(self):
        return f"{self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table = "parohijani"
        verbose_name = "Парохијан"
        verbose_name_plural = "Парохијани"
