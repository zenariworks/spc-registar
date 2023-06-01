"""
Model class for representing menus in the database.
"""
from django.db import models


class Menu(models.Model):
    men_rbr = models.IntegerField()
    men_sifra = models.TextField()
    men_naziv = models.TextField()
    men_nivo = models.TextField()
    men_kod = models.IntegerField()
    men_flag = models.TextField()

    def __str__(self):
        return f"{self.men_rbr}"

    class Meta:
        managed = True
        db_table = "meni"
