"""
Model class for representing slavas in the database.
"""
from django.db import models


class Slava(models.Model):
    sl_rbr = models.IntegerField()
    sl_sifra = models.IntegerField()
    sl_naziv = models.TextField()
    sl_dan = models.IntegerField()
    sl_mesec = models.IntegerField()
    sl_akt = models.TextField()
    sl_flag = models.TextField()

    def __str__(self):
        return f"{self.sl_rbr}"

    class Meta:
        managed = True
        db_table = "slave"
