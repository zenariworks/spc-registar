"""Модул модела особе у бази података."""

from django.db import models

from .adresa import Adresa
from .base import TimestampedModel
from .slava import Slava


class Osoba(TimestampedModel):
    """Класа која представља особу (парохијанин или друга особа из црквених записа)."""

    uid = models.AutoField(primary_key=True, unique=True, editable=False)

    ime = models.CharField(max_length=100, verbose_name="име")
    prezime = models.CharField(max_length=100, verbose_name="презиме")

    devojacko_prezime = models.CharField(
        max_length=100, verbose_name="девојачко презиме", blank=True, null=True
    )

    parohijan = models.BooleanField(
        default=False, verbose_name="парохијан", help_text="Да ли је особа парохијанин"
    )

    # Подаци специфични за парохијане (опционо за остале)
    adresa = models.ForeignKey(
        Adresa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="адреса"
    )
    slava = models.ForeignKey(
        Slava, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="слава"
    )
    tel_fiksni = models.CharField(
        max_length=20, verbose_name="фиксни телефон", blank=True, null=True
    )
    tel_mobilni = models.CharField(
        max_length=20, verbose_name="мобилни телефон", blank=True, null=True
    )
    slavska_vodica = models.BooleanField(default=False, verbose_name="славска водица")
    uskrsnja_vodica = models.BooleanField(default=False, verbose_name="ускршња водица")

    # Основни подаци о особи
    mesto_rodjenja = models.CharField(
        max_length=100, verbose_name="место рођења", blank=True, null=True
    )
    datum_rodjenja = models.DateField(
        verbose_name="датум рођења", blank=True, null=True
    )
    vreme_rodjenja = models.TimeField(
        verbose_name="време рођења", blank=True, null=True
    )
    pol = models.CharField(
        max_length=1,
        verbose_name="пол",
        choices=[("М", "мушки"), ("Ж", "женски")],
        blank=True,
        null=True,
    )

    zanimanje = models.CharField(
        max_length=100, verbose_name="занимање", blank=True, null=True
    )
    veroispovest = models.CharField(
        max_length=50, verbose_name="вероисповест", blank=True, null=True
    )
    narodnost = models.CharField(
        max_length=50, verbose_name="народност", blank=True, null=True
    )

    def __str__(self):
        return f"{self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table = "osobe"
        verbose_name = "Особа"
        verbose_name_plural = "Особе"


# Alias за компатибилност уназад
Parohijan = Osoba
