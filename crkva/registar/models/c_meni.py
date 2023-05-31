from django.db import models


class hspmeni(models.Model):
    men_rbr = models.IntegerField()
    men_sifra = models.TextField()
    men_naziv = models.TextField()
    men_nivo = models.TextField()
    men_kod = models.IntegerField()
    men_flag = models.TextField()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        managed = True
        db_table = "meni"
