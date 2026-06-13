"""Издавалац преписа — потпис у подножју крштенице/венчанице (#278).

Подножје преписа потписује корисник који *издаје* документ (пријављени
корисник), а не нужно свештеник који је обавио чин. Овај модул разрешава
потпис и парохију издаваоца, са фолбеком када пријављени корисник нема
везан свештенички профил.
"""

from __future__ import annotations

from typing import Any


def get_izdavalac(request) -> dict[str, Any]:
    """Враћа ``{"potpis", "parohija"}`` за подножје преписа.

    - Ако пријављени корисник има везан ``Svestenik`` профил → пун потпис
      (звање, име, презиме) и његова парохија.
    - Иначе фолбек: назив парохије тренутног тенанта + приказно име
      корисника (без свештеничке титуле); празни стрингови ако ништа.
    """
    user = getattr(request, "user", None)
    # Реверзни OneToOne: Django-ов дескриптор наслеђује AttributeError када
    # веза не постоји, па ``getattr(..., None)`` безбедно враћа None.
    svestenik = getattr(user, "svestenik", None)
    if svestenik is not None:
        return {"potpis": svestenik, "parohija": svestenik.parohija}

    tenant = getattr(request, "tenant", None)
    parohija = getattr(tenant, "parohija_naziv", "") or getattr(tenant, "naziv", "")
    if user is not None and getattr(user, "is_authenticated", False):
        potpis = user.get_full_name() or user.get_username()
    else:
        potpis = ""
    return {"potpis": potpis, "parohija": parohija}
