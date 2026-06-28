"""Приказ календара слава са информацијом о посту."""

from __future__ import annotations

import calendar
import datetime as dt
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from kalendar.models import Slava
from registar.kalendar import WEEKDAY_LABELS, build_day_cell
from registar.models import Domacinstvo
from registar.utils import MESECI

# crkvenikalendar.rs uses Cyrillic-month-name spelled in Latin script in the URL.
# Map our 1..12 to the slug they use:
CRKVENIKALENDAR_MONTH_SLUG = {
    1: "januar",
    2: "februar",
    3: "mart",
    4: "april",
    5: "maj",
    6: "jun",
    7: "jul",
    8: "avgust",
    9: "septembar",
    10: "oktobar",
    11: "novembar",
    12: "decembar",
}


def crkvenikalendar_url(year: int, month: int) -> str:
    """URL of the month page on crkvenikalendar.rs (Serbian Orthodox calendar)."""
    slug = CRKVENIKALENDAR_MONTH_SLUG.get(month)
    return f"https://crkvenikalendar.rs/{slug}-{year}/" if slug else ""


@login_required
def kalendar(
    request: HttpRequest, year: int | None = None, month: int | None = None
) -> HttpResponse:
    """Приказ месеца са славама и обележеним данима поста.

    Подразумевана година је текућа година,
    а подразумевани месец је текући месец.
    """

    today = dt.date.today()
    year = year or today.year
    month = month or today.month

    # Припрема календара дана у месецу
    first_weekday, days_in_month = calendar.monthrange(year, month)  # Mon=0 .. Sun=6
    days = [dt.date(year, month, d) for d in range(1, days_in_month + 1)]

    # Фиксне славе за тражени месец, груписане по дану
    slave_za_mesec = (
        Slava.objects.filter(mesec=month)
        .annotate(dom_count=Count("domacinstvo"))
        .order_by("dan", "naziv")
    )
    by_day: dict[int, list[Slava]] = defaultdict(list)
    for s in slave_za_mesec:
        if s.dan:
            by_day[s.dan].append(s)

    # Покретне славе - рачунамо за сваку и проверавамо да ли пада у тражени месец
    pokretne_slave = (
        Slava.objects.filter(pokretni=True)
        .annotate(dom_count=Count("domacinstvo"))
        .order_by("offset_nedelje", "offset_dani", "naziv")
    )
    for s in pokretne_slave:
        datum = s.get_datum(year)
        if datum and datum.month == month:
            # Васкрс нико не слави као крсну славу (dom_count=0); за
            # календарску значку прикажи број домаћинстава васкршње
            # водице, што води на обједињену страницу (#325).
            if s.je_vaskrs:
                s.dom_count = Domacinstvo.objects.filter(vaskrsnja_vodica=True).count()
            by_day[datum.day].append(s)

    # Ћелије са водећим празним местима за поравнање испод заглавља дана
    # (заједничка логика у registar.kalendar)
    cells = []
    for _ in range(first_weekday):
        cells.append({"is_placeholder": True})
    for d in days:
        cell = build_day_cell(d, by_day.get(d.day, []), today)
        cell["is_placeholder"] = False
        cells.append(cell)

    # Навигација за претходни/наредни месец
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        "year": year,
        "month": month,
        "month_name": MESECI.get(month, str(month)),
        "month_label": f"{MESECI.get(month, str(month))} {year}",
        "source_url": crkvenikalendar_url(year, month),
        "weekday_labels": WEEKDAY_LABELS,
        "cells": cells,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }

    return render(request, "registar/kalendar.html", context)
