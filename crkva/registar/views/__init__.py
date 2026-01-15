"""Модул за приказе у апликацији регистар."""

import datetime as dt
from collections import defaultdict

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from registar.models import Parohijan, Slava, Veroispovest
from registar.utils import get_query_variants
from registar.utils_fasting import get_fasting_type

from .domacinstvo_view import PrikazDomacinstva, SpisakDomacinsta
from .kalendar_view import kalendar
from .krstenje_view import KrstenjePDF, PrikazKrstenja, SpisakKrstenja, unos_krstenja
from .parohijan_view import (
    ParohijanPDF,
    PrikazParohijana,
    SpisakParohijana,
    unos_parohijana,
)
from .slava_view import slava_domacinstva
from .svestenik_view import PrikazSvestenika, SpisakSvestenika, SvestenikPDF
from .vencanje_view import (
    PrikazVencanja,
    SpisakVencanja,
    VencanjePDF,
    calibrate_vencanje,
    unos_vencanja,
)
from .view_404 import custom_404


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
    weekday_labels = ["Пон", "Уто", "Сре", "Чет", "Пет", "Суб", "Нед"]

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

    context = {
        "calendar_cells": cells,
    }

    return render(request, "registar/index.html", context)


def search_view(request) -> HttpResponse:
    """
    Претрага вероисповести, парохијана и домаћинстава.
    """
    query = request.GET.get("query", "")
    variants = get_query_variants(query) if query else []
    # Build Q for Veroисповест
    q_vero = None
    if variants:
        for v in variants:
            clause = Q(naziv__icontains=v)
            q_vero = clause if q_vero is None else (q_vero | clause)
    elif query:
        q_vero = Q(naziv__icontains=query)

    # Build Q for Парохијан
    q_par = None
    if variants:
        for v in variants:
            clause = Q(ime__icontains=v) | Q(prezime__icontains=v)
            q_par = clause if q_par is None else (q_par | clause)
    elif query:
        q_par = Q(ime__icontains=query) | Q(prezime__icontains=query)

    context = {
        "query": query,
        "veroisposvest_results": (
            Veroispovest.objects.filter(q_vero)
            if q_vero
            else Veroispovest.objects.none()
        ),
        "parohijan_results": (
            Parohijan.objects.filter(q_par) if q_par else Parohijan.objects.none()
        ),
    }

    return render(request, "registar/search_view.html", context)


__all__ = [
    "index",
    "search_view",
    "kalendar",
    "custom_404",
    "unos_krstenja",
    "unos_parohijana",
    "unos_vencanja",
    "calibrate_vencanje",
    "SpisakParohijana",
    "PrikazParohijana",
    "SpisakDomacinsta",
    "PrikazDomacinstva",
    "SpisakKrstenja",
    "PrikazKrstenja",
    "SpisakVencanja",
    "PrikazVencanja",
    "SpisakSvestenika",
    "PrikazSvestenika",
    "VencanjePDF",
    "ParohijanPDF",
    "KrstenjePDF",
    "SvestenikPDF",
    "slava_domacinstva",
]
