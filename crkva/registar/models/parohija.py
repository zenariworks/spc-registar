import uuid

from django.db import models

from .crkvena_opstina import CrkvenaOpstina


class Parohija(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    naziv = models.CharField(max_length=200, verbose_name="назив")
    crkvena_opstina = models.ForeignKey(
        CrkvenaOpstina,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="црквена општина",
    )

    def __str__(self) -> str:
        return f"{self.naziv}, {self.crkvena_opstina}"

    class Meta:
        managed = True
        db_table: str = "parohije"
        verbose_name: str = "Парохија"
        verbose_name_plural: str = "Парохије"
