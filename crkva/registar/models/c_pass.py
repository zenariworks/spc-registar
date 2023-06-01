"""
Model class for representing passes in the database.
"""

from django.db import models


class HSPPASS(models.Model):
    pas_rbr = models.IntegerField()
    pas_sifra = models.IntegerField()
    pas_naziv = models.TextField()
    pas_nivo = models.IntegerField()
    pas_flag = models.TextField()

    def __str__(self):
        return f"{self.pas_naziv}"

    class Meta:
        managed = True
        db_table = "passes"
