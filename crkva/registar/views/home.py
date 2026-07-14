"""Почетна страница — приказ календарског прегледа актуелних слава."""

import datetime as dt
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from registar.kalendar import WEEKDAY_LABELS, build_day_cell
from registar.models import Slava
from registar.views.search import _get_registry_stats


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
        "pomak_nedelje", "pomak_dani", "naziv"
    )
    year = today.year
    for s in pokretne_slave:
        datum = s.get_datum(year)
        if datum:
            by_day[(datum.month, datum.day)].append(s)

    # Изградња ћелија (заједничка логика у registar.kalendar)
    cells = []
    for d in days:
        cell = build_day_cell(d, by_day.get((d.month, d.day), []), today)
        if d == today:
            cell["day_label"] = "данас"
        elif d == today - dt.timedelta(days=1):
            cell["day_label"] = "јуче"
        elif d == today + dt.timedelta(days=1):
            cell["day_label"] = "сутра"
        else:
            cell["day_label"] = WEEKDAY_LABELS[d.weekday()]
        cell["is_yesterday"] = d == today - dt.timedelta(days=1)
        cell["is_upcoming"] = d > today
        cells.append(cell)

    # Split cells for the home page: today gets the hero, the next 5 days
    # form the upcoming-list. (calendar_cells stays full for backwards compat.)
    today_cell = next((c for c in cells if c["is_today"]), None)
    upcoming_cells = [c for c in cells if c["date"] > today]

    context = {
        "stats": _get_registry_stats(),
        "calendar_cells": cells,
        "today_cell": today_cell,
        "upcoming_cells": upcoming_cells,
    }

    return render(request, "registar/index.html", context)
