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

    Изузетак је Васкрс (покретни празник Васкрсења): нико га не слави као
    крсну славу, па уместо празног списка по слави приказујемо домаћинства
    васкршње водице (`vaskrsnja_vodica=True`) — иста страница за #26 и #27.
    Приказ је исти као списак домаћинстава по слави (по улицама, са
    члановима), само је основни скуп васкршња водица, филтриран по парохији
    изабраног свештеника (веза домаћинство→парохија иде преко
    `adresa.svestenik.parohija`, #325).
    """
    slava = get_object_or_404(Slava, uid=uid)

    svestenik = resolve_svestenik(request)
    selected_id = (request.GET.get("svestenik") or "").strip()
    nema_parohije = svestenik is not None and not svestenik.parohija_id

    # За Васкрс списак крсне славе је увек празан; приказујемо домаћинства
    # означена за васкршњу водицу (једна страница уместо две — #325).
    je_vaskrs = slava.je_vaskrs
    base_qs = (
        Domacinstvo.objects.filter(vaskrsnja_vodica=True)
        if je_vaskrs
        else Domacinstvo.objects.filter(slava=slava)
    )

    # Понуди у избору само свештенике чија парохија заиста има домаћинстава у
    # овом приказу — свештеник без домаћинстава дао би празан списак, па га
    # не нудимо (територија се додељује преко `Adresa.svestenik`, #325).
    parohije_sa_domacinstvima = set(
        base_qs.filter(adresa__svestenik__parohija__isnull=False)
        .values_list("adresa__svestenik__parohija_id", flat=True)
        .distinct()
    )
    svestenici = [
        s
        for s in Svestenik.objects.filter(parohija__isnull=False)
        .select_related("parohija")
        .order_by("prezime", "ime")
        if s.parohija_id in parohije_sa_domacinstvima
    ]

    # Households celebrating this slava, optionally narrowed to the selected
    # priest's parish (territory resolved by parish, not by priest — #26).
    domacinstva = list(
        by_parish_filter(
            base_qs.select_related("domacin", "adresa").prefetch_related(
                "ukucani", "ukucani__osoba"
            ),
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
        "je_vaskrs": je_vaskrs,
    }

    return render(request, "registar/slava_domacinstva.html", context)
