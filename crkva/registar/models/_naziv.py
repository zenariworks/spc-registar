"""Заједничка основа за lookup моделе са нормализованим `naziv`.

Narodnost/Zanimanje/Veroispovest нормализују `naziv` у `save()`, али
`bulk_create`/`bulk_update` заобилазе `save()`, па case-insensitive
ограничење (`*_naziv_ci_uniq`) може да пропусти дупликате са вишком
размака или другачијом величином слова (#298). Овај QuerySet нормализује
`naziv` и на тим bulk путањама, па ограничење важи без обзира на пут уписа.

Напомена: `QuerySet.update()` (SQL UPDATE без учитавања редова у Python)
се не покрива — за то нема безбедне генеричке нормализације; готово сав
упис ионако иде кроз форме или `save()`.
"""

from __future__ import annotations

import uuid

from django.db import models
from django.db.models.functions import Lower
from registar.utils.tekst import normalizuj


class NazivQuerySet(models.QuerySet):
    """QuerySet који нормализује `naziv` на bulk путањама."""

    def bulk_create(self, objs, *args, **kwargs):
        objs = list(objs)
        for obj in objs:
            if getattr(obj, "naziv", None):
                obj.naziv = normalizuj(obj.naziv)
        return super().bulk_create(objs, *args, **kwargs)

    def bulk_update(self, objs, fields, *args, **kwargs):
        if "naziv" in fields:
            for obj in objs:
                if getattr(obj, "naziv", None):
                    obj.naziv = normalizuj(obj.naziv)
        return super().bulk_update(objs, fields, *args, **kwargs)


class NazivModel(models.Model):
    """Апстрактна основа шифарника (Narodnost/Veroispovest/Zanimanje).

    Даје `uid`, `naziv` са case-insensitive јединственим ограничењем
    `<модел>_naziv_ci_uniq` и нормализацију `naziv` у `save()`, да
    ограничење не пропусти дупликате са вишком размака (#252).
    Подкласе могу поново да декларишу `naziv` ради другачијег `verbose_name`.
    """

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    naziv = models.CharField(verbose_name="назив", max_length=255)

    objects = NazivQuerySet.as_manager()

    def __str__(self):
        return f"{self.naziv}"

    def save(self, *args, **kwargs):
        if self.naziv:
            self.naziv = normalizuj(self.naziv)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(Lower("naziv"), name="%(class)s_naziv_ci_uniq"),
        ]
