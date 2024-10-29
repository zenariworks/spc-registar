"""Модул модела славе у бази података."""

from django.db import models

from .dan import Dan
from .mesec import Mesec


class Slava(models.Model):
    """Класа која представља слава."""

    uid = models.IntegerField(primary_key=True, unique=True, editable=False)

    naziv = models.CharField(verbose_name="назив")
    opsti_naziv = models.CharField(verbose_name="општи назив")

    dan = models.ForeignKey(
        Dan, verbose_name="дан", on_delete=models.SET_NULL, null=True
    )
    mesec = models.ForeignKey(
        Mesec,
        verbose_name="месец",
        on_delete=models.SET_NULL,
        null=True,
        to_field="mesec",
    )

    # def __str__(self):
    #     return f"{self.dan}. {self.mesec}: {self.naziv}"
    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "slave"
        verbose_name = "Слава"
        verbose_name_plural = "Славе"
