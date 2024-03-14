import re
import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Drzava(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(max_length=100, verbose_name="назив")
    postkod_regex = models.CharField(
        max_length=128, verbose_name="регекс поштанског броја"
    )

    def __str__(self):
        return self.naziv

    class Meta:
        managed = True
        db_table = "drzave"
        verbose_name = "Држава"
        verbose_name_plural = "Државе"

    @staticmethod
    def validiraj_postanski_broj(pib, regex):
        if not re.match(regex, pib):
            raise ValidationError("Поштански број не одговара формату државе.")
