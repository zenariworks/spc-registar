"""Views for displaying households celebrating a specific slava."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from registar.models import Domacinstvo, Slava, Svestenik
from registar.views.roster import group_by_street, partition_zivi_preminuli
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
    """
    slava = get_object_or_404(Slava, uid=uid)

    # Only priests with a parish can drive the territory filter (we filter
    # households by the priest's parish), so omit parish-less priests (#27).
    svestenici = list(
        Svestenik.objects.filter(parohija__isnull=False)
        .select_related("parohija")
        .order_by("prezime", "ime")
    )
    svestenik = resolve_svestenik(request)
    selected_id = (request.GET.get("svestenik") or "").strip()
    nema_parohije = svestenik is not None and not svestenik.parohija_id

    # Households celebrating this slava, optionally narrowed to the selected
    # priest's parish (territory resolved by parish, not by priest — #26).
    # За Васкрс списак крсне славе је увек празан; приказујемо домаћинства
    # означена за васкршњу водицу (једна страница уместо две — #325).
    je_vaskrs = slava.je_vaskrs
    base_qs = (
        Domacinstvo.objects.filter(vaskrsnja_vodica=True)
        if je_vaskrs
        else Domacinstvo.objects.filter(slava=slava)
    )
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
        d.zivi_clanovi, d.preminuli_clanovi = partition_zivi_preminuli(d.ukucani.all())

    # Group households by street for the printed report (issue #18); queryset
    # is already ordered by adresa__ulica.
    grupe = group_by_street(domacinstva)

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
