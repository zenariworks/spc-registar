import uuid

from django.db import models


class Eparhija(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=100, verbose_name="назив")
    sediste = models.CharField(max_length=100, verbose_name="седиште")
    episkop = models.CharField(max_length=100, verbose_name="епископ")

    def __str__(self):
        return self.naziv
    
    class Meta:
        managed = True
        db_table = "eparhije"
        verbose_name = "Епархија"
        verbose_name_plural = "Епархије"
