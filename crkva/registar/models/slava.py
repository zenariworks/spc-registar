"""Модул модела славе у бази података."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Slava(models.Model):
    """Класа која представља слава."""

    uid = models.AutoField(primary_key=True, unique=True, editable=False)

    naziv = models.CharField(verbose_name="назив")
    opsti_naziv = models.CharField(verbose_name="општи назив")

    dan = models.IntegerField(
        verbose_name="дан",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        null=True,
        blank=True,
    )
    mesec = models.IntegerField(
        verbose_name="месец",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        null=True,
        blank=True,
    )

    def get_mesec_naziv(self):
        """Враћа назив месеца."""
        from registar.utils import MESECI
        return MESECI.get(self.mesec, "") if self.mesec else ""

    def __str__(self):
        return f"{self.naziv}"

    class Meta:
        managed = True
        db_table = "slave"
        verbose_name = "Слава"
        verbose_name_plural = "Славе"
