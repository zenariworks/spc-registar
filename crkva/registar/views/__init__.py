"""Модул за приказе у апликацији регистар."""

import datetime as dt
from collections import defaultdict

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from registar.models import Domacinstvo, Krstenje, Parohijan, Slava, Svestenik, Vencanje
from registar.utils import get_query_variants
from registar.utils_fasting import get_fasting_type

from .domacinstvo_view import PrikazDomacinstva, SpisakDomacinsta
from .kalendar_view import kalendar
from .krstenje_view import (
    KrstenjePDF,
    PrikazKrstenja,
    SpisakKrstenja,
    calibrate_krstenje,
    unos_krstenja,
)
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

__all__ = [
    # Re-exports for url config and other modules
    "PrikazDomacinstva",
    "SpisakDomacinsta",
    "kalendar",
    "KrstenjePDF",
    "PrikazKrstenja",
    "SpisakKrstenja",
    "calibrate_krstenje",
    "unos_krstenja",
    "ParohijanPDF",
    "PrikazParohijana",
    "SpisakParohijana",
    "unos_parohijana",
    "slava_domacinstva",
    "PrikazSvestenika",
    "SpisakSvestenika",
    "SvestenikPDF",
    "PrikazVencanja",
    "SpisakVencanja",
    "VencanjePDF",
    "calibrate_vencanje",
    "unos_vencanja",
    "custom_404",
    # Functions defined in this module
    "index",
    "search_view",
    "search_autocomplete",
]


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
        "stats": {
            "parohijani": Parohijan.objects.count(),
            "krstenja": Krstenje.objects.count(),
            "vencanja": Vencanje.objects.count(),
            "svestenici": Svestenik.objects.count(),
        },
        "calendar_cells": cells,
    }

    return render(request, "registar/index.html", context)


SEARCH_PREVIEW_LIMIT = 5


def search_view(request) -> HttpResponse:
    """Глобална претрага по свим ентитетима."""
    query = request.GET.get("query", "").strip()
    variants = get_query_variants(query) if query else []

    def build_q(fields):
        """Прави Q објекат за дата поља и варијанте претраге."""
        q = Q()
        for v in variants:
            for field in fields:
                q |= Q(**{f"{field}__icontains": v})
        return q

    if variants:
        parohijani_qs = (
            Parohijan.objects.filter(build_q(["ime", "prezime"]))
            .select_related("adresa")
            .distinct()
        )
        svestenici_qs = (
            Svestenik.objects.filter(build_q(["ime", "prezime", "zvanje"]))
            .select_related("parohija")
            .distinct()
        )
        krstenja_qs = (
            Krstenje.objects.filter(
                build_q(
                    [
                        "dete__ime",
                        "otac__ime",
                        "otac__prezime",
                        "majka__ime",
                        "majka__prezime",
                    ]
                )
            )
            .select_related("dete", "otac", "majka")
            .distinct()
        )
        vencanja_qs = (
            Vencanje.objects.filter(
                build_q(
                    ["zenik__ime", "zenik__prezime", "nevesta__ime", "nevesta__prezime"]
                )
            )
            .select_related("zenik", "nevesta")
            .distinct()
        )
        domacinstva_qs = (
            Domacinstvo.objects.filter(
                build_q(["domacin__ime", "domacin__prezime", "adresa__ulica"])
            )
            .select_related("domacin", "adresa", "slava")
            .distinct()
        )
    else:
        parohijani_qs = Parohijan.objects.none()
        svestenici_qs = Svestenik.objects.none()
        krstenja_qs = Krstenje.objects.none()
        vencanja_qs = Vencanje.objects.none()
        domacinstva_qs = Domacinstvo.objects.none()

    # Get total counts per type
    counts = {
        "parohijani": parohijani_qs.count(),
        "svestenici": svestenici_qs.count(),
        "krstenja": krstenja_qs.count(),
        "vencanja": vencanja_qs.count(),
        "domacinstva": domacinstva_qs.count(),
    }
    total = sum(counts.values())

    context = {
        "stats": {
            "parohijani": Parohijan.objects.count(),
            "krstenja": Krstenje.objects.count(),
            "vencanja": Vencanje.objects.count(),
            "svestenici": Svestenik.objects.count(),
        },
        "query": query,
        "total": total,
        "parohijani": parohijani_qs[:SEARCH_PREVIEW_LIMIT],
        "parohijani_count": counts["parohijani"],
        "svestenici": svestenici_qs[:SEARCH_PREVIEW_LIMIT],
        "svestenici_count": counts["svestenici"],
        "krstenja": krstenja_qs[:SEARCH_PREVIEW_LIMIT],
        "krstenja_count": counts["krstenja"],
        "vencanja": vencanja_qs[:SEARCH_PREVIEW_LIMIT],
        "vencanja_count": counts["vencanja"],
        "domacinstva": domacinstva_qs[:SEARCH_PREVIEW_LIMIT],
        "domacinstva_count": counts["domacinstva"],
    }

    return render(request, "registar/search_view.html", context)


def search_autocomplete(request):
    """JSON endpoint за аутокомплит претрагу — grouped by type, ranked by relevance."""
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"groups": []})

    variants = get_query_variants(query)

    def build_q(fields):
        q = Q()
        for v in variants:
            for field in fields:
                q |= Q(**{f"{field}__icontains": v})
        return q

    def rank_item(text):
        """Start-of-name matches rank 0, contains matches rank 1."""
        text_lower = text.lower()
        for v in variants:
            if text_lower.startswith(v.lower()):
                return 0
        return 1

    groups = []

    # Парохијани
    parohijani = list(
        Parohijan.objects.filter(build_q(["ime", "prezime"])).distinct()[:10]
    )
    if parohijani:
        items = sorted(
            [
                {
                    "text": f"{p.ime} {p.prezime}",
                    "sub": str(p.datum_rodjenja or ""),
                    "url": f"/parohijan/{p.uid}/",
                    "_rank": rank_item(f"{p.ime} {p.prezime}"),
                }
                for p in parohijani
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Парохијани", "items": items})

    # Свештеници
    svestenici = list(
        Svestenik.objects.filter(build_q(["ime", "prezime"])).distinct()[:10]
    )
    if svestenici:
        items = sorted(
            [
                {
                    "text": f"{s.ime} {s.prezime}",
                    "sub": s.zvanje,
                    "url": f"/svestenik/{s.uid}/",
                    "_rank": rank_item(f"{s.ime} {s.prezime}"),
                }
                for s in svestenici
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Свештеници", "items": items})

    # Крштења
    krstenja = list(
        Krstenje.objects.filter(
            build_q(["dete__ime", "otac__ime", "otac__prezime", "majka__ime"])
        )
        .select_related("dete", "otac", "majka")
        .distinct()[:10]
    )
    if krstenja:
        items = sorted(
            [
                {
                    "text": f"{k.ime_deteta} {k.prezime_oca}",
                    "sub": str(k.datum or ""),
                    "url": f"/krstenje/{k.uid}/",
                    "_rank": rank_item(k.ime_deteta or ""),
                }
                for k in krstenja
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Крштења", "items": items})

    # Венчања
    vencanja = list(
        Vencanje.objects.filter(
            build_q(
                ["zenik__ime", "zenik__prezime", "nevesta__ime", "nevesta__prezime"]
            )
        )
        .select_related("zenik", "nevesta")
        .distinct()[:10]
    )
    if vencanja:
        items = sorted(
            [
                {
                    "text": f"{v.ime_zenika} и {v.ime_neveste} {v.prezime_zenika}",
                    "sub": str(v.datum or ""),
                    "url": f"/vencanje/{v.uid}/",
                    "_rank": rank_item(v.ime_zenika or ""),
                }
                for v in vencanja
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Венчања", "items": items})

    return JsonResponse({"groups": groups})
