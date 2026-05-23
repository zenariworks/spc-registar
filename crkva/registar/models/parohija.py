"""Модул модела парохије у бази података."""

import uuid

from django.db import models

from .crkvena_opstina import CrkvenaOpstina


class Parohija(models.Model):
    """Класа која представља парохија."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=200, verbose_name="назив")
    crkvena_opstina = models.ForeignKey(
        CrkvenaOpstina,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="црквена општина",
    )

    _ROMAN_DIGITS = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}

    def __str__(self) -> str:
        # Legacy data: a single digit naziv was rendered as the matching
        # roman numeral. For any other (and now far more common) naziv,
        # return the actual value so admin dropdowns / select2 widgets /
        # history pages do not render the empty string.
        if self.naziv in self._ROMAN_DIGITS:
            return self._ROMAN_DIGITS[self.naziv]
        return self.naziv or ""

    class Meta:
        managed = True
        db_table: str = "parohije"
        verbose_name: str = "Парохија"
        verbose_name_plural: str = "Парохије"
