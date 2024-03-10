from django.http import HttpResponse
from django.shortcuts import redirect, render
from registar.forms import VeroispovestForm
from registar.models import Veroispovest

from .krstenje_view import KrstenjePDF, PrikazKrstenja, SpisakKrstenja
from .parohijan_view import ParohijanPDF, PrikazParohijana, SpisakParohijana
from .svestenik_view import PrikazSvestenika, SpisakSvestenika, SvestenikPDF
from .vencanje_view import PrikazVencanja, SpisakVencanja, VencanjePDF
from .view_404 import custom_404


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


# In your views.py
def search_view(request) -> HttpResponse:
    query = request.GET.get("query", "")
    if query:
        results = Veroispovest.objects.filter(naziv__icontains=query)
    else:
        results = Veroispovest.objects.none()

    return render(
        request=request,
        template_name="registar/search_view.html",
        context={"results": results},
    )


__all__ = [
    "index",
    "dodaj_izmeni_veroispovest",
    "search_view",
    "custom_404",
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
