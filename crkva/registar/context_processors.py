from datetime import timedelta
from django.utils import timezone
from typing import Any

from .models import Slava
from .utils_fasting import is_fasting_day


def processor_narednih_slava(request) -> dict[str, Any]:
    """
    Контекст процесор који враћа:
    - јучерашње славе
    - данашње славе
    - славе за наредних 7 дана (груписане по датуму)
    """
    danas = timezone.now()

    # Јуче
    juce = danas - timedelta(days=1)
    juce_slave = list(Slava.objects.filter(dan=juce.day, mesec=juce.month))
    juce_post = is_fasting_day(juce.date())

    # Данас
    danas_slave = list(Slava.objects.filter(dan=danas.day, mesec=danas.month))
    danas_post = is_fasting_day(danas.date())

    # Наредних 7 дана (без данас)
    narednih_dani = [danas + timedelta(days=i) for i in range(1, 8)]
    narednih_slave: list[dict[str, Any]] = []
    for datum in narednih_dani:
        slave_na_datum = list(Slava.objects.filter(dan=datum.day, mesec=datum.month))
        if slave_na_datum:
            narednih_slave.append({
                "datum": datum,
                "slave": slave_na_datum,
                "post": is_fasting_day(datum.date()),
            })

    return {
        "juce_slave": juce_slave,
        "danas_slave": danas_slave,
        "narednih_slave": narednih_slave,
        "juce_post": juce_post,
        "danas_post": danas_post,
        "broj_juce": len(juce_slave),
        "broj_danas": len(danas_slave),
        "juce_datum": juce,
        "danas_datum": danas,
    }
