"""
Model class for representing slavas in the database.
"""
import uuid

from django.db import models

from .dan import Dan
from .mesec import Mesec


class Slava(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(verbose_name="назив")
    opsti_naziv = models.CharField(verbose_name="општи назив")

    dan = models.ForeignKey(Dan, verbose_name="дан", on_delete=models.CASCADE)
    mesec = models.ForeignKey(
        Mesec, verbose_name="месец", on_delete=models.CASCADE, to_field="mesec"
    )

    def __str__(self):
        return f"{self.dan}. {self.mesec}: {self.naziv}"

    class Meta:
        managed = True
        db_table = "slave"
        verbose_name = "Слава"
        verbose_name_plural = "Славе"
