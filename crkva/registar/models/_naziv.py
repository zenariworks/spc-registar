"""Заједнички QuerySet за lookup моделе са нормализованим `naziv`.

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

from django.db import models
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
