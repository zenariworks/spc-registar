"""
Model class for representing weddings in the database.
"""
from django.db import models


class Vencanje(models.Model):
    v_rbr = models.IntegerField()
    v_sifra = models.IntegerField()
    v_aktgod = models.IntegerField()
    v_knjiga = models.IntegerField()
    v_strana = models.IntegerField()
    v_tekbroj = models.IntegerField()
    v_datum = models.TextField()
    v_z_ime = models.TextField()
    v_z_prez = models.TextField()
    v_z_zanim = models.TextField()
    v_z_mesto = models.TextField()
    v_z_verois = models.TextField()
    v_z_narodn = models.TextField()
    v_z_adresa = models.TextField()
    v_n_ime = models.TextField()
    v_n_prez = models.TextField()
    v_n_zanim = models.TextField()
    v_n_mesto = models.TextField()
    v_n_verois = models.TextField()
    v_n_narodn = models.TextField()
    v_n_adresa = models.TextField()
    v_zr_otac = models.TextField()
    v_zr_majka = models.TextField()
    v_nr_otac = models.TextField()
    v_nr_majka = models.TextField()
    v_z_rodjg = models.IntegerField()
    v_z_rodjm = models.IntegerField()
    v_z_rodjd = models.IntegerField()
    v_z_rodjme = models.TextField()
    v_n_rodjg = models.IntegerField()
    v_n_rodjm = models.IntegerField()
    v_n_rodjd = models.IntegerField()
    v_n_rodjme = models.TextField()
    v_z_brak = models.IntegerField()
    v_n_brak = models.IntegerField()
    v_ispitgod = models.IntegerField()
    v_ispitmes = models.IntegerField()
    v_ispitdan = models.IntegerField()
    v_godina = models.IntegerField()
    v_mesec = models.IntegerField()
    v_dan = models.IntegerField()
    v_hrmesto = models.TextField()
    v_hrime = models.TextField()
    v_rbrsvest = models.IntegerField()
    v_svestime = models.TextField()
    v_svestcin = models.TextField()
    v_svestpar = models.TextField()
    v_kum = models.TextField()
    v_ssvat = models.TextField()
    v_razrdn = models.TextField()
    v_razrtxt = models.TextField()

    def __str__(self):
        return f"{self.v_rbr}"

    class Meta:
        managed = True
        db_table = "vencanja"
