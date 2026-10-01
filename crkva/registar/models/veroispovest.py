"""Модул модела вероисповести у бази података."""

from django.db import models
from registar.models._naziv import NazivModel


class Veroispovest(NazivModel):
    """Класа која представља вероисповести."""

    naziv = models.CharField(verbose_name="вероисповест", max_length=255)

    class Meta(NazivModel.Meta):
        db_table = "veroispovesti"
        verbose_name = "Вероисповест"
        verbose_name_plural = "Вероисповести"
