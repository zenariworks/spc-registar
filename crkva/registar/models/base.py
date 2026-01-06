"""
Базни модел са заједничким пољима за све моделе.
"""

from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
    """
    Апстрактни базни модел који додаје временске ознаке свим моделима.

    Поља:
        created_at: Време креирања записа (аутоматски се поставља при креирању)
        updated_at: Време последње измене (аутоматски се ажурира при свакој измени)
    """

    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="креирано",
        help_text="Време креирања записа",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="измењено",
        help_text="Време последње измене",
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
