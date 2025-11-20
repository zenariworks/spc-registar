"""Приказ календара слава са информацијом о посту."""

from __future__ import annotations

import calendar
import datetime as dt
from collections import defaultdict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from registar.models import Slava
from registar.utils import MESECI
from registar.utils_fasting import is_fasting_day, get_fasting_type


def slava_kalendar(request: HttpRequest, year: int | None = None, month: int | None = None) -> HttpResponse:
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
    slave_za_mesec = Slava.objects.filter(mesec=month).order_by("dan", "naziv")
    by_day: dict[int, list[Slava]] = defaultdict(list)
    for s in slave_za_mesec:
        if s.dan:
            by_day[s.dan].append(s)

    # Покретне славе - рачунамо за сваку и проверавамо да ли пада у тражени месец
    pokretne_slave = Slava.objects.filter(pokretni=True).order_by("offset_nedelje", "offset_dani", "naziv")
    for s in pokretne_slave:
        datum = s.get_datum(year)
        if datum and datum.month == month:
            by_day[datum.day].append(s)

    # Обогаћени подаци за темплат
    # Weekday labels (Mon..Sun) in Serbian abbreviations
    weekday_labels = ["Пон", "Уто", "Сре", "Чет", "Пет", "Суб", "Нед"]

    # Major feast days (important observances)
    MAJOR_FEASTS = {
        (1, 7): "Божић",  # Christmas
        (1, 19): "Богојављење",  # Epiphany
        (8, 28): "Велика Госпојина",  # Dormition
        (9, 21): "Мала Госпојина",  # Nativity of Theotokos
        (11, 21): "Ваведење",  # Presentation of Mary
        (1, 27): "Свети Сава",  # Saint Sava
        (12, 19): "Свети Никола",  # Saint Nicholas
        (5, 19): "Ђурђевдан",  # Saint George
    }

    # Build cells with leading placeholders to align under weekday headers
    cells = []
    for _ in range(first_weekday):
        cells.append({"is_placeholder": True})
    for d in days:
        fasting_info = get_fasting_type(d)
        day_slavas = by_day.get(d.day, [])

        # Check if this is a major feast day
        is_important = (d.month, d.day) in MAJOR_FEASTS
        # Also check if any slava name contains major keywords
        if day_slavas and not is_important:
            for slava in day_slavas:
                slava_lower = slava.naziv.lower()
                if any(keyword in slava_lower for keyword in ['васкрс', 'спасовдан', 'тројице', 'духови', 'вазнесењ']):
                    is_important = True
                    break

        cells.append(
            {
                "is_placeholder": False,
                "date": d,
                "weekday_label": weekday_labels[d.weekday()],
                "is_fasting": fasting_info['is_fasting'],
                "fasting_type": fasting_info['type'],
                "fasting_display": fasting_info['display'],
                "fasting_description": fasting_info['description'],
                "slave": day_slavas,
                "is_important": is_important,
                "is_today": d == today,
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