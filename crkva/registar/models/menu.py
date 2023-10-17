"""
Model class for representing menus in the database.
"""
import uuid

from django.db import models


class Menu(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.TextField()
    naziv = models.TextField()
    nivo = models.TextField()
    kod = models.IntegerField()
    flag = models.TextField()

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "meni"
        verbose_name = "Мени"
        verbose_name_plural = "Мени"
