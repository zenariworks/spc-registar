"""Модул модела укућана у бази података."""

from django.db import models

from .base import TimestampedModel
from .domacinstvo import Domacinstvo
from .parohijan import Osoba


class Ukucanin(TimestampedModel):
    domacinstvo = models.ForeignKey(
        Domacinstvo, on_delete=models.CASCADE, related_name="ukucani"
    )

    osoba = models.ForeignKey(
        Osoba,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="особа",
    )

    # Резервно име ако особа није повезана (за старије преминуле)
    ime_ukucana = models.CharField(max_length=255, blank=True, null=True)

    uloga = models.CharField(
        max_length=30,
        choices=[
            ("домаћин", "Домаћин"),
            ("супружник", "Супружник/ка"),
            ("дете", "Дете"),
            ("рођак", "Рођак/сродник"),
            ("остало", "Остало"),
        ],
        default="остало",
    )

    preminuo = models.BooleanField(default=False, verbose_name="преминуо")

    def __str__(self):
        status = " (+)" if self.preminuo else ""
        if self.osoba:
            return f"{self.osoba}{status} ({self.get_uloga_display()})"
        return f"{self.ime_ukucana}{status} ({self.get_uloga_display()})"

    class Meta:
        db_table = "ukucani"
        verbose_name = "Укућанин"
        verbose_name_plural = "Укућани"
        constraints = [
            models.UniqueConstraint(
                fields=["domacinstvo", "osoba"],
                condition=models.Q(osoba__isnull=False),
                name="unique_osoba_per_domacinstvo",
            )
        ]
