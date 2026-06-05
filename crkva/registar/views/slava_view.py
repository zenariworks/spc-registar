"""Views for displaying households celebrating a specific slava."""

from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from registar.models import Domacinstvo, Slava, Svestenik
from registar.views.territory import by_parish_filter, resolve_svestenik


@login_required
def slava_domacinstva(request: HttpRequest, uid: int) -> HttpResponse:
    """Приказује домаћинства која славе одређену славу.

    Опциони филтер `?svestenik=<uid>` сужава приказ на парохију изабраног
    свештеника (славска водица по свештенику, #27) — корисно да свештеник
    испланира обилазак свечара дате славе по улицама своје парохије.
    """
    slava = get_object_or_404(Slava, uid=uid)

    svestenici = list(Svestenik.objects.order_by("prezime", "ime"))
    svestenik = resolve_svestenik(request)
    selected_id = (request.GET.get("svestenik") or "").strip()
    nema_parohije = svestenik is not None and not svestenik.parohija_id

    # Households celebrating this slava, optionally narrowed to the selected
    # priest's parish (territory resolved by parish, not by priest — #26).
    domacinstva = list(
        by_parish_filter(
            Domacinstvo.objects.filter(slava=slava)
            .select_related("domacin", "adresa")
            .prefetch_related("ukucani", "ukucani__osoba"),
            svestenik,
        ).order_by(
            "adresa__ulica",
            "adresa__broj",
            "domacin__prezime",
            "domacin__ime",
        )
    )

    # Attach partitioned lists so the template can render living vs.
    # deceased as two columns without needing custom template tags.
    for d in domacinstva:
        members = list(d.ukucani.all())
        d.zivi_clanovi = [u for u in members if not u.preminuo]
        d.preminuli_clanovi = [u for u in members if u.preminuo]

    # Group households by street for the printed report (issue #18). The
    # queryset is already ordered by adresa__ulica, so consecutive items share
    # a street; households without an address fall into a trailing group.
    def _street(d):
        if d.adresa and (d.adresa.ulica or "").strip():
            return d.adresa.ulica.strip()
        return ""

    grupe = [
        {"ulica": ulica or "Без улице", "domacinstva": list(items)}
        for ulica, items in groupby(domacinstva, key=_street)
    ]

    context = {
        "slava": slava,
        "domacinstva": domacinstva,
        "grupe": grupe,
        "count": len(domacinstva),
        "svestenici": svestenici,
        "svestenik": svestenik,
        "selected_id": selected_id,
        "nema_parohije": nema_parohije,
    }

    return render(request, "registar/slava_domacinstva.html", context)
