"""Свештеник → територија (парохија) филтер за приказе домаћинстава (#26).

Улице су додељене свештеницима преко `Adresa.svestenik`, али свештеници
ротирају — стабилна јединица територије је ПАРОХИЈА. Зато домаћинства
филтрирамо по парохији изабраног свештеника, а не по самом свештенику.

Дели се између приказа домаћинстава (`domacinstvo_view`), васкршње водице
(#26) и славске водице по свештенику (#27).
"""

from __future__ import annotations

from django.http import HttpRequest
from registar.models import Svestenik


def resolve_svestenik(request: HttpRequest):
    """Свештеник из ?svestenik=<uid>, или None ако није изабран/невалидан."""
    val = (request.GET.get("svestenik") or "").strip()
    if not val:
        return None
    try:
        return Svestenik.objects.filter(pk=int(val)).first()
    except (ValueError, TypeError):
        return None


def by_parish_filter(qs, svestenik):
    """Сужава `qs` домаћинстава на парохију изабраног свештеника (#26).

    - без свештеника → `qs` непромењен (сва домаћинства),
    - свештеник са парохијом → `adresa.svestenik.parohija` == његова парохија,
    - свештеник без парохије → празан `qs` (нема територију за приказ).
    """
    if svestenik is not None and svestenik.parohija_id:
        return qs.filter(adresa__svestenik__parohija=svestenik.parohija_id)
    if svestenik is not None:
        return qs.none()
    return qs
