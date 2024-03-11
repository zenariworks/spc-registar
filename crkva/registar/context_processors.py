from datetime import datetime, timedelta
from typing import Any

from .models import Dan, Mesec, Slava


def processor_narednih_slava(request) -> dict[str, list[Any]]:
    danas = datetime.now()
    naredni_dani = [danas + timedelta(days=i) for i in range(7)]

    naredne_slave = []

    for datum in naredni_dani:
        dan = Dan.objects.get(dan=datum.day)
        mesec = Mesec.objects.get(mesec=datum.month)
        slava = Slava.objects.filter(dan=dan, mesec=mesec)
        naredne_slave.extend(slava)

    return {"naredne_slave": naredne_slave}
