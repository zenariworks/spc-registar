from datetime import datetime, timedelta
from typing import Any

from .models import Slava


def processor_narednih_slava(request) -> dict[str, list[Any]]:
    danas = datetime.now()
    naredni_dani = [danas + timedelta(days=i) for i in range(7)]

    naredne_slave = []

    for datum in naredni_dani:
        slava = Slava.objects.filter(dan=datum.day, mesec=datum.month)
        naredne_slave.extend(slava)

    return {"naredne_slave": naredne_slave}
