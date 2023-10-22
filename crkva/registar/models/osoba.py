"""
Model class for representing sets in the database.
"""
import uuid

from django.db import models


class Osoba(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    ime = models.CharField(verbose_name="име")
    prezime = models.CharField(verbose_name="презиме")
    devojacko_prezime = models.CharField(verbose_name="девојачко презиме")
    datum_rodjenja = models.DateTimeField(verbose_name="датум рођења")
    mesto_rodjenja = models.CharField(verbose_name="место рођења")

    pol = models.CharField(verbose_name="пол", blank=True)
    zanimanje = models.CharField(verbose_name="занимање", blank=True)
    veroispovest = models.CharField(verbose_name="вероисповест", blank=True)
    narodnost = models.CharField(verbose_name="народност", blank=True)
    adresa = models.CharField(verbose_name="адреса", blank=True)


    def __str__(self):
        return f"{self.ime} {self.prezime}"

    class Meta:
        managed = True
        db_table = "osobe"
        verbose_name = "Особа"
        verbose_name_plural = "Особе"
