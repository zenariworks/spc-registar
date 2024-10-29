"""Модул модела адресе у бази података."""

import uuid

from django.db import models

from .ulica import Ulica


class Adresa(models.Model):
    """Класа која представља адресе."""

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    broj = models.CharField(max_length=10, verbose_name="број")
    sprat = models.CharField(max_length=10, verbose_name="спрат", null=True, blank=True)
    broj_stana = models.CharField(
        max_length=10, verbose_name="број_стана", null=True, blank=True
    )
    dodatak = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="додатак"
    )
    postkod = models.CharField(
        max_length=10, verbose_name="поштански број", null=True, blank=True
    )
    primedba = models.TextField(blank=True, null=True, verbose_name="примедба")
    ulica = models.ForeignKey(Ulica, on_delete=models.CASCADE, verbose_name="улица")

    def clean(self):
        """Валидација поштанског броја."""
        if self.postkod and self.ulica and self.ulica.drzava:
            self.ulica.drzava.provera_postkoda(self.postkod)

    def __str__(self):
        detalji = f"{self.ulica.naziv} {self.broj}"
        detalji += f"/{self.sprat}" if self.sprat else ""
        detalji += f"/{self.broj_stana}" if self.broj_stana else ""
        detalji += f"/{self.dodatak}" if self.dodatak else ""
        detalji += f", {self.postkod}" if self.postkod else ""
        detalji += f", {self.ulica.mesto}" if self.ulica.mesto else ""
        detalji += f", {self.ulica.opstina}" if self.ulica.opstina else ""
        detalji += f", {self.ulica.drzava}" if self.ulica.drzava else ""
        detalji += f" (Примедба: {self.primedba})" if self.primedba else ""
        return detalji

    class Meta:
        managed = True
        db_table = "adrese"
        verbose_name = "Адреса"
        verbose_name_plural = "Адресе"
