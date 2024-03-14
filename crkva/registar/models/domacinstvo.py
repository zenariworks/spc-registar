"""
Класа модела за представљање домаћинстава у бази података.
"""

import uuid

from django.db import models

from .adresa import Adresa
from .parohijan import Parohijan
from .slava import Slava

# from phonenumber_field.modelfields import PhoneNumberField


class Domacinstvo(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    domacin = models.ForeignKey(
        Parohijan, on_delete=models.CASCADE, null=False, verbose_name="домаћин"
    )
    adresa = models.ForeignKey(
        Adresa, on_delete=models.SET_NULL, null=True, verbose_name="адреса"
    )
    tel_fiksni = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="тел. фиксни"
    )
    tel_mobilni = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="тел. мобилни"
    )
    slava = models.ForeignKey(
        Slava, on_delete=models.SET_NULL, null=True, verbose_name="слава"
    )
    slavska_vodica = models.BooleanField(default=False, verbose_name="славска водица")
    uskrsnja_vodica = models.BooleanField(default=False, verbose_name="ускршња водица")
    napomena = models.TextField(blank=True, null=True, verbose_name="напомена")

    def __str__(self) -> str:
        return f"{self.domacin.prezime}"

    class Meta:
        managed = True
        db_table: str = "domacinstva"
        verbose_name: str = "Домаћинство"
        verbose_name_plural: str = "Домаћинства"
