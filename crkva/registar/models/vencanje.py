"""
Model class for representing weddings in the database.
"""
import uuid

from django.db import models

from .dan import Dan
from .mesec import Mesec


class Vencanje(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.IntegerField()
    aktgod = models.IntegerField()
    knjiga = models.IntegerField()
    strana = models.IntegerField()
    tekbroj = models.IntegerField()
    datum = models.DateField()
    z_ime = models.CharField()
    z_prez = models.CharField()
    z_zanim = models.CharField()
    z_mesto = models.CharField()
    z_verois = models.CharField()
    z_narodn = models.CharField()
    z_adresa = models.CharField()
    n_ime = models.CharField()
    n_prez = models.CharField()
    n_zanim = models.CharField()
    n_mesto = models.CharField()
    n_verois = models.CharField()
    n_narodn = models.CharField()
    n_adresa = models.CharField()
    zr_otac = models.CharField()
    zr_majka = models.CharField()
    nr_otac = models.CharField()
    nr_majka = models.CharField()
    z_rodjg = models.IntegerField()
    z_rodjm = models.IntegerField()
    z_rodjd = models.IntegerField()
    z_rodjme = models.CharField()
    n_rodjg = models.IntegerField()
    n_rodjm = models.IntegerField()
    n_rodjd = models.IntegerField()
    n_rodjme = models.CharField()
    z_brak = models.IntegerField()
    n_brak = models.IntegerField()
    ispitgod = models.IntegerField()
    ispitmes = models.IntegerField()
    ispitdan = models.IntegerField()
    godina = models.IntegerField()
    mesec = models.ForeignKey(Mesec, on_delete=models.CASCADE, name="месец")
    dan = models.ForeignKey(Dan, on_delete=models.CASCADE, name="дан")
    shrmesto = models.TextField()
    shrime = models.TextField()
    srbrsvest = models.IntegerField()
    ssvestime = models.CharField()
    ssvestcin = models.CharField()
    ssvestpar = models.CharField()
    sssvat = models.CharField()
    srazrdn = models.TextField()
    srazrtxt = models.TextField()

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "vencanja"
        verbose_name = "Венчање"
        verbose_name_plural = "Венчања"
