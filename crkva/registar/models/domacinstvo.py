"""
Model class for representing households in the database.
"""
import uuid

from django.db import models
# from phonenumber_field.modelfields import PhoneNumberField

from .slava import Slava
from .adresa import Adresa
from .parohijan import Parohijan


class Domacinstvo(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    domacin = models.ForeignKey(Parohijan, on_delete=models.SET_NULL, null=True, verbose_name="домаћин")
    adresa = models.ForeignKey(Adresa, on_delete=models.SET_NULL, null=True, verbose_name="адреса")

    oznaka = models.CharField()
    tel_fiksni = models.CharField(blank=True, null=True, verbose_name="тел. фиксни")
    tel_mobilni = models.CharField(blank=True, null=True, verbose_name="тел. мобилни")

    slava = models.ForeignKey(Slava, on_delete=models.SET_NULL, null=True, verbose_name="слава")

    napomena = models.TextField(null=True, verbose_name="напомена")

    def __str__(self) -> str:
        return f"{self.uid}"

    class Meta:
        managed = True
        db_table: str = "domacinstva"
        verbose_name: str = "Домаћинство"
        verbose_name_plural: str = "Домаћинства"
