"""Модул модела народности у бази података."""

from django.db import models
from registar.models._naziv import NazivModel


class Narodnost(NazivModel):
    """Класа која представља народности."""

    naziv = models.CharField(verbose_name="народност", max_length=255)

    class Meta(NazivModel.Meta):
        db_table = "narodnosti"
        verbose_name = "Народност"
        verbose_name_plural = "Народности"
