"""Почетна страница — приказ календарског прегледа актуелних слава."""

import datetime as dt
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from registar.models import Krstenje, Osoba, Slava, Svestenik, Vencanje
from registar.utils_fasting import get_fasting_type


@login_required
def index(request) -> HttpResponse:
    """
    Приказ почетне странице са календарским приказом актуелних слава (-1 до +5 дана).
    """
    today = dt.date.today()

    # Generate dates from yesterday to +5 days
    days = []
    for offset in range(-1, 6):
        day_date = today + dt.timedelta(days=offset)
        days.append(day_date)

    # Fetch fixed slavas for all months we need
    months_needed = set(d.month for d in days)
    slave_by_month = {}
    for month in months_needed:
        slave_by_month[month] = list(
            Slava.objects.filter(mesec=month).order_by("dan", "naziv")
        )

    # Group fixed slavas by (month, day)
    by_day = defaultdict(list)
    for month, slave_list in slave_by_month.items():
        for s in slave_list:
            if s.dan:
                by_day[(month, s.dan)].append(s)

    # Add moveable slavas
    pokretne_slave = Slava.objects.filter(pokretni=True).order_by(
        "offset_nedelje", "offset_dani", "naziv"
    )
    year = today.year
    for s in pokretne_slave:
        datum = s.get_datum(year)
        if datum:
            by_day[(datum.month, datum.day)].append(s)

    # Build cells for template
    weekday_labels = ["пон", "уто", "сре", "чет", "пет", "суб", "нед"]

    # Major feast days
    major_feasts = {
        (1, 7): "Божић",
        (1, 19): "Богојављење",
        (8, 28): "Велика Госпојина",
        (9, 21): "Мала Госпојина",
        (11, 21): "Ваведење",
        (1, 27): "Свети Сава",
        (12, 19): "Свети Никола",
        (5, 19): "Ђурђевдан",
    }

    cells = []
    for d in days:
        fasting_info = get_fasting_type(d)
        day_slavas = by_day.get((d.month, d.day), [])

        # Separate fixed and moveable feasts
        fixed_slavas = [s for s in day_slavas if not s.pokretni]
        moveable_slavas = [s for s in day_slavas if s.pokretni]

        # Check if this day has a "crveno slovo" (red letter day) observance
        is_crveno_slovo = any(s.crveno_slovo for s in day_slavas)

        # Check if major feast
        is_important = (d.month, d.day) in major_feasts
        if day_slavas and not is_important:
            for slava in day_slavas:
                slava_lower = slava.naziv.lower()
                if any(
                    keyword in slava_lower
                    for keyword in [
                        "васкрс",
                        "спасовдан",
                        "тројице",
                        "духови",
                        "вазнесењ",
                    ]
                ):
                    is_important = True
                    break

        # Determine day label
        if d == today:
            day_label = "данас"
        elif d == today - dt.timedelta(days=1):
            day_label = "јуче"
        elif d == today + dt.timedelta(days=1):
            day_label = "сутра"
        else:
            day_label = weekday_labels[d.weekday()]

        cells.append(
            {
                "date": d,
                "weekday_label": weekday_labels[d.weekday()],
                "day_label": day_label,
                "is_fasting": fasting_info["is_fasting"],
                "fasting_type": fasting_info["type"],
                "fasting_class": {
                    "вода": "water",
                    "уље": "oil",
                    "риба": "fish",
                    "бели_мрс": "dairy",
                }.get(fasting_info["type"])
                or "",
                "fasting_display": fasting_info["display"],
                "fasting_description": fasting_info["description"],
                "slave": day_slavas,
                "fixed_slavas": fixed_slavas,
                "moveable_slavas": moveable_slavas,
                "is_important": is_important,
                "is_crveno_slovo": is_crveno_slovo,
                "is_today": d == today,
                "is_yesterday": d == today - dt.timedelta(days=1),
                "is_upcoming": d > today,
            }
        )

    # Split cells for the home page: today gets the hero, the next 5 days
    # form the upcoming-list. (calendar_cells stays full for backwards compat.)
    today_cell = next((c for c in cells if c["is_today"]), None)
    upcoming_cells = [c for c in cells if c["date"] > today]

    context = {
        "stats": {
            "parohijani": Osoba.objects.count(),
            "krstenja": Krstenje.objects.count(),
            "vencanja": Vencanje.objects.count(),
            "svestenici": Svestenik.objects.count(),
        },
        "calendar_cells": cells,
        "today_cell": today_cell,
        "upcoming_cells": upcoming_cells,
    }

    return render(request, "registar/index.html", context)
