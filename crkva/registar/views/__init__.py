"""Модул за приказе у апликацији регистар."""

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from registar.models import Parohijan, Veroispovest
from registar.utils import get_query_variants

from .krstenje_view import KrstenjePDF, PrikazKrstenja, SpisakKrstenja, unos_krstenja
from .parohijan_view import (
    ParohijanPDF,
    PrikazParohijana,
    SpisakParohijana,
    unos_parohijana,
)
from .svestenik_view import PrikazSvestenika, SpisakSvestenika, SvestenikPDF
from .vencanje_view import PrikazVencanja, SpisakVencanja, VencanjePDF, unos_vencanja
from .view_404 import custom_404
from .slava_calendar_view import slava_kalendar


def index(request) -> HttpResponse:
    """
    Приказ почетне странице.
    """
    return render(request, "registar/index.html")


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
            Veroispovest.objects.filter(q_vero) if q_vero else Veroispovest.objects.none()
        ),
        "parohijan_results": (
            Parohijan.objects.filter(q_par) if q_par else Parohijan.objects.none()
        ),
    }

    return render(request, "registar/search_view.html", context)


__all__ = [
    "index",
    "search_view",
    "slava_kalendar",
    "custom_404",
    "unos_krstenja",
    "unos_parohijana",
    "unos_vencanja",
    "SpisakParohijana",
    "PrikazParohijana",
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
]
