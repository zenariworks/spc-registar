"""
Model class for representing households in the database.
"""
import uuid

from django.db import models

from .slava import Slava


class Domacinstvo(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    sifra = models.IntegerField()
    ime = models.CharField()
    ukuc = models.TextField()
    rbrul = models.IntegerField()
    ulbroj = models.IntegerField()
    broj = models.IntegerField()
    oznaka = models.CharField()
    stan = models.IntegerField()
    teldir = models.IntegerField()
    telmob = models.IntegerField()

    slava = models.ForeignKey(Slava, on_delete=models.CASCADE, name="слава")

    slavod = models.CharField()
    uskvod = models.CharField()
    napom = models.CharField()
    akt = models.CharField()
    flag = models.CharField()

    def __str__(self):
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table = "domacinstva"
        verbose_name = "Домаћинство"
        verbose_name_plural = "Домаћинства"
