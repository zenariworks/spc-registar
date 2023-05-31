from django.db import models


class hspslave(models.Model):
    sl_rbr = models.IntegerField()
    sl_sifra = models.IntegerField()
    sl_naziv = models.TextField()
    sl_dan = models.IntegerField()
    sl_mesec = models.IntegerField()
    sl_akt = models.TextField()
    sl_flag = models.TextField()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        managed = True
        db_table = "slave"
