"""Извештај — преглед домаћинстава за васкршњу водицу по улицама (#26).

За изабраног свештеника (улице су му додељене преко `Adresa.svestenik`)
издваја домаћинства са `vaskrsnja_vodica=True`, групише их по улици и
приказује број домаћинстава по улици — згодно за планирање обиласка.
"""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from registar.models import Domacinstvo, Svestenik


@login_required
def vaskrsnja_vodica(request: HttpRequest) -> HttpResponse:
    """Приказ улица и броја домаћинстава за васкршњу водицу по свештенику."""
    svestenici = list(Svestenik.objects.order_by("prezime", "ime"))

    selected = (request.GET.get("svestenik") or "").strip()
    svestenik = None
    if selected:
        try:
            svestenik = next(s for s in svestenici if str(s.pk) == selected)
        except StopIteration:
            svestenik = None

    redovi = []
    ukupno = 0
    # Улице су додељене свештеницима, али свештеници ротирају — стабилна
    # јединица територије је ПАРОХИЈА. Зато извештај за изабраног свештеника
    # обухвата све улице његове парохије (било ком свештенику те парохије да
    # су историјски додељене).
    nema_parohije = svestenik is not None and not svestenik.parohija_id
    if svestenik is not None and svestenik.parohija_id:
        qs = (
            Domacinstvo.objects.filter(
                vaskrsnja_vodica=True,
                adresa__svestenik__parohija=svestenik.parohija_id,
            )
            .values("adresa__ulica")
            .annotate(broj=Count("uid"))
            .order_by("adresa__ulica")
        )
        for row in qs:
            ulica = (row["adresa__ulica"] or "").strip() or "Без улице"
            redovi.append({"ulica": ulica, "broj": row["broj"]})
        ukupno = sum(r["broj"] for r in redovi)

    context = {
        "svestenici": svestenici,
        "selected_id": selected,
        "svestenik": svestenik,
        "nema_parohije": nema_parohije,
        "redovi": redovi,
        "ukupno": ukupno,
        "broj_ulica": len(redovi),
    }
    return render(request, "registar/vaskrsnja_vodica.html", context)
