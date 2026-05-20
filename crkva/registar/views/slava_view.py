"""Views for displaying households celebrating a specific slava."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from registar.models import Domacinstvo, Slava


@login_required
def slava_domacinstva(request: HttpRequest, uid: int) -> HttpResponse:
    """Приказује домаћинства која славе одређену славу."""
    slava = get_object_or_404(Slava, uid=uid)

    # Get all households celebrating this slava
    domacinstva = list(
        Domacinstvo.objects.filter(slava=slava)
        .select_related("domacin", "adresa")
        .prefetch_related("ukucani", "ukucani__osoba")
        .order_by("domacin__prezime", "domacin__ime")
    )

    # Attach partitioned lists so the template can render living vs.
    # deceased as two columns without needing custom template tags.
    for d in domacinstva:
        members = list(d.ukucani.all())
        d.zivi_clanovi = [u for u in members if not u.preminuo]
        d.preminuli_clanovi = [u for u in members if u.preminuo]

    context = {
        "slava": slava,
        "domacinstva": domacinstva,
        "count": len(domacinstva),
    }

    return render(request, "registar/slava_domacinstva.html", context)
