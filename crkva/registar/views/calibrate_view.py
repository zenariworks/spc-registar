"""Заједнички приказ алата за калибрацију штампаних образаца (#16).

Један шаблон (``registar/calibrate.html``) и једна функција за обе врсте
(крштеница/венчаница); конкретни погледи само прослеђују врсту.
"""

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from registar.calibration import CALIBRATIONS


def render_calibrate(request, kind):
    """Рендерује калибрациони шаблон за дату врсту обрасца (``kind``)."""
    if not settings.CALIBRATION_ENABLED:
        raise Http404("Калибрација је искључена.")
    cfg = CALIBRATIONS[kind]
    return render(
        request,
        "registar/calibrate.html",
        {
            "cal_title": cfg["title"],
            "cal_css": cfg["css"],
            "cal_bg": cfg["bg"],
            "cal_prefix": cfg["prefix"],
            "cal_fields": cfg["fields"],
        },
    )
