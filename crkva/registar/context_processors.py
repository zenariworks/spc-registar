from datetime import timedelta
from django.utils import timezone
from typing import Any

from .models import Slava


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

    # Данас
    danas_slave = list(Slava.objects.filter(dan=danas.day, mesec=danas.month))

    # Наредних 7 дана (без данас)
    narednih_dani = [danas + timedelta(days=i) for i in range(1, 8)]
    narednih_slave: list[dict[str, Any]] = []
    for datum in narednih_dani:
        slave_na_datum = list(Slava.objects.filter(dan=datum.day, mesec=datum.month))
        if slave_na_datum:
            narednih_slave.append({
                "datum": datum,
                "slave": slave_na_datum,
            })

    return {
        "juce_slave": juce_slave,
        "danas_slave": danas_slave,
        "narednih_slave": narednih_slave,
    }
