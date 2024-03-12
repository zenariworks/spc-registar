from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from registar.forms import VeroispovestForm
from registar.models import Domacinstvo, Parohijan, Veroispovest

from .krstenje_view import KrstenjePDF, PrikazKrstenja, SpisakKrstenja
from .parohijan_view import (
    ParohijanPDF,
    PrikazParohijana,
    SpisakParohijana,
    create_parohijan,
)
from .svestenik_view import PrikazSvestenika, SpisakSvestenika, SvestenikPDF
from .vencanje_view import PrikazVencanja, SpisakVencanja, VencanjePDF
from .view_404 import custom_404


def prikazi_domacinstva(request, uid):
    domacinstva = Domacinstvo.objects.filter(slava__uid=uid)
    return render(
        request, "registar/spisak_domacinstava.html", {"domacinstva": domacinstva}
    )


def index(request) -> HttpResponse:
    return render(request, "registar/index.html")


def dodaj_izmeni_veroispovest(request, uid=None):
    if uid:
        veroispovest = Veroispovest.objects.get(uid=uid)
        form = VeroispovestForm(request.POST or None, instance=veroispovest)
    else:
        form = VeroispovestForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("nekigde")

    return render(
        request=request,
        template_name="registar/form_veroispovest.html",
        context={"form": form},
    )


def search_view(request) -> HttpResponse:
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
        # Pretpostavljamo da želite pretraživati po napomenama domaćinstva
        "domacinstvo_results": (
            Domacinstvo.objects.filter(napomena__icontains=query)
            if query
            else Domacinstvo.objects.none()
        ),
    }

    return render(request, "registar/search_view.html", context)


__all__ = [
    "index",
    "dodaj_izmeni_veroispovest",
    "search_view",
    "custom_404",
    "create_parohijan",
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
