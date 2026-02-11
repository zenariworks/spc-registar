"""Views for displaying households celebrating a specific slava."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from registar.models import Domacinstvo, Slava


def slava_domacinstva(request: HttpRequest, uid: int) -> HttpResponse:
    """Приказује домаћинства која славе одређену славу."""
    slava = get_object_or_404(Slava, uid=uid)

    # Get all households celebrating this slava
    domacinstva = (
        Domacinstvo.objects.filter(slava=slava)
        .select_related("domacin", "adresa", "adresa__ulica")
        .prefetch_related("ukucani", "ukucani__osoba")
        .order_by("domacin__prezime", "domacin__ime")
    )

    context = {
        "slava": slava,
        "domacinstva": domacinstva,
        "count": domacinstva.count(),
    }

    return render(request, "registar/slava_domacinstva.html", context)
