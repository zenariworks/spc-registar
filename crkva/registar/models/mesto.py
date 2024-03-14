import uuid

from django.db import models

from .opstina import Opstina


class Mesto(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(max_length=100, verbose_name="назив")
    opstina = models.ForeignKey(
        Opstina,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="општина",
    )

    def __str__(self):
        return f"{self.naziv}, {self.opstina}"

    class Meta:
        managed = True
        db_table = "mesta"
        verbose_name = "Место"
        verbose_name_plural = "Места"
