from datetime import datetime, timedelta

from .models import Dan
from .models import Mesec
from .models import Slava


def upcoming_slavas_processor(request):
    today = datetime.now()
    upcoming_dates = [today + timedelta(days=i) for i in range(7)]
    
    upcoming_slavas = []

    for date in upcoming_dates:
        day = Dan.objects.get(dan=date.day)
        month = Mesec.objects.get(mesec=date.month)
        slavas_on_date = Slava.objects.filter(dan=day, mesec=month)
        upcoming_slavas.extend(slavas_on_date)

    return {'upcoming_slavas': upcoming_slavas}
