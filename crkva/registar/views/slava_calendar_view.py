"""Приказ календара слава са информацијом о посту."""

from __future__ import annotations

import calendar
import datetime as dt
from collections import defaultdict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from registar.models import Slava
from registar.utils import MESECI
from registar.utils_fasting import is_fasting_day


def slava_kalendar(request: HttpRequest, year: int | None = None, month: int | None = None) -> HttpResponse:
    """Приказ месеца са славама и обележеним данима поста.

    Подразумевана година је 2025. (према референци календара поста),
    а подразумевани месец је текући месец.
    """

    today = dt.date.today()
    year = year or 2025
    month = month or today.month

    # Припрема календара дана у месецу
    first_weekday, days_in_month = calendar.monthrange(year, month)  # Mon=0 .. Sun=6
    days = [dt.date(year, month, d) for d in range(1, days_in_month + 1)]

    # Славе за тражени месец, груписане по дану
    slave_za_mesec = Slava.objects.filter(mesec=month).order_by("dan", "naziv")
    by_day: dict[int, list[Slava]] = defaultdict(list)
    for s in slave_za_mesec:
        if s.dan:
            by_day[s.dan].append(s)

    # Обогаћени подаци за темплат
    # Weekday labels (Mon..Sun) in Serbian abbreviations
    weekday_labels = ["Пон", "Уто", "Сре", "Чет", "Пет", "Суб", "Нед"]

    # Build cells with leading placeholders to align under weekday headers
    cells = []
    for _ in range(first_weekday):
        cells.append({"is_placeholder": True})
    for d in days:
        cells.append(
            {
                "is_placeholder": False,
                "date": d,
                "weekday_label": weekday_labels[d.weekday()],
                "is_fasting": is_fasting_day(d),
                "slave": by_day.get(d.day, []),
            }
        )

    # Навигација за претходни/наредни месец
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        "year": year,
        "month": month,
        "month_name": MESECI.get(month, str(month)),
        "weekday_labels": weekday_labels,
        "cells": cells,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    }

    return render(request, "registar/slava_kalendar.html", context)