"""Модул модела укућана у бази података."""

from django.db import models

#from .domacinstvo import Domacinstvo
from .parohijan import Parohijan


class Ukucanin(models.Model):
    """Класа која представља укућана."""

    parohijan = models.ForeignKey(
        Parohijan, on_delete=models.CASCADE, verbose_name="парохијан"
    )
    # domacinstvo = models.ForeignKey(
    #     Domacinstvo, on_delete=models.CASCADE, null=True, verbose_name="домаћинство"
    # )
    uloga = models.CharField(max_length=255, verbose_name="улога", blank=True)

    def __str__(self) -> str:
        return f"{self.parohijan} - {self.uloga} у {self.domacinstvo}"

    class Meta:
        managed = True
        db_table = "ukucani"
        verbose_name = "Укућанин"
        verbose_name_plural = "Укућани"
