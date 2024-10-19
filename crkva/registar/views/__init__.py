"""Модул за приказе у апликацији регистар."""
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from registar.models import Parohijan, Veroispovest

from .krstenje_view import KrstenjePDF, PrikazKrstenja, SpisakKrstenja, unos_krstenja
from .parohijan_view import (
    ParohijanPDF,
    PrikazParohijana,
    SpisakParohijana,
    unos_parohijana,
)
from .svestenik_view import PrikazSvestenika, SpisakSvestenika, SvestenikPDF
from .vencanje_view import PrikazVencanja, SpisakVencanja, VencanjePDF
from .view_404 import custom_404


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
    context = {
        "query": query,
        "veroisposvest_results": (
            Veroispovest.objects.filter(naziv__icontains=query)
            if query
            else Veroispovest.objects.none()
        ),
        "parohijan_results": (
            Parohijan.objects.filter(
                Q(ime__icontains=query) | Q(prezime__icontains=query)
            )
            if query
            else Parohijan.objects.none()
        ),
    }

    return render(request, "registar/search_view.html", context)


__all__ = [
    "index",
    "search_view",
    "custom_404",
    "unos_krstenja",
    "unos_parohijana",
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
