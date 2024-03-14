"""
Класа модела за представљање адресе у бази података.
"""

import re
import uuid

from django.db import models
from django.forms import ValidationError

from .ulica import Ulica


class Adresa(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    ulica = models.ForeignKey(Ulica, on_delete=models.CASCADE, verbose_name="улица")
    broj = models.CharField(max_length=10, verbose_name="број")
    dodatak = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="додатак"
    )
    postkod = models.CharField(
        max_length=10, verbose_name="поштански број", null=True, blank=True
    )
    napomena = models.TextField(blank=True, null=True, verbose_name="напомена")

    def clean(self):
        """Валидација постанског броја."""
        if self.postkod and self.ulica.mesto.opstina.drzava:
            regex = self.ulica.mesto.opstina.drzava.postkod_regex
            if not re.match(regex, self.postkod):
                raise ValidationError("Поштански број не одговара формату државе.")

    def __str__(self):
        detalji = f"{self.ulica.naziv} {self.broj}"
        if self.dodatak:
            detalji += f"/{self.dodatak}"
        detalji += f", {self.ulica.mesto}"
        if self.napomena:
            detalji += f" (Напомена: {self.napomena})"
        return detalji

    class Meta:
        managed = True
        db_table = "adrese"
        verbose_name = "Адреса"
        verbose_name_plural = "Адресе"
