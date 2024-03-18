"""
Класа модела за представљање адресе у бази података.
"""

import uuid

from django.db import models

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
        """Валидација поштанског броја."""
        if self.postkod and self.ulica and self.ulica.drzava:
            self.ulica.drzava.provera_postkoda(self.postkod)

    def __str__(self):
        detalji = f"{self.ulica.naziv} {self.broj}"
        detalji += f"/{self.dodatak}" if self.dodatak else ""
        detalji += f", {self.postkod}" if self.postkod else ""
        detalji += f", {self.ulica.mesto}" if self.ulica.mesto else ""
        detalji += f", {self.ulica.opstina}" if self.ulica.opstina else ""
        detalji += f", {self.ulica.drzava}" if self.ulica.drzava else ""
        detalji += f" (Напомена: {self.napomena})" if self.napomena else ""
        return detalji

    class Meta:
        managed = True
        db_table = "adrese"
        verbose_name = "Адреса"
        verbose_name_plural = "Адресе"
