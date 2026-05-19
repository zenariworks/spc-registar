"""Глобална претрага и AJAX аутокомплетер."""

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from registar.models import (
    Domacinstvo,
    Krstenje,
    Parohijan,
    Slava,
    Svestenik,
    Vencanje,
)
from registar.utils import get_query_variants


SEARCH_PREVIEW_LIMIT = 5


def search_view(request) -> HttpResponse:
    """Глобална претрага по свим ентитетима."""
    query = request.GET.get("query", "").strip()
    variants = get_query_variants(query) if query else []

    def build_q(fields):
        """Прави Q објекат за дата поља и варијанте претраге."""
        q = Q()
        for v in variants:
            for field in fields:
                q |= Q(**{f"{field}__icontains": v})
        return q

    if variants:
        parohijani_qs = (
            Parohijan.objects.filter(build_q(["ime", "prezime"]))
            .select_related("adresa")
            .distinct()
        )
        svestenici_qs = (
            Svestenik.objects.filter(build_q(["ime", "prezime", "zvanje"]))
            .select_related("parohija")
            .distinct()
        )
        krstenja_qs = (
            Krstenje.objects.filter(
                build_q(
                    [
                        "dete__ime",
                        "otac__ime",
                        "otac__prezime",
                        "majka__ime",
                        "majka__prezime",
                    ]
                )
            )
            .select_related("dete", "otac", "majka")
            .distinct()
        )
        vencanja_qs = (
            Vencanje.objects.filter(
                build_q(
                    ["zenik__ime", "zenik__prezime", "nevesta__ime", "nevesta__prezime"]
                )
            )
            .select_related("zenik", "nevesta")
            .distinct()
        )
        domacinstva_qs = (
            Domacinstvo.objects.filter(
                build_q(["domacin__ime", "domacin__prezime", "adresa__ulica"])
            )
            .select_related("domacin", "adresa", "slava")
            .distinct()
        )
    else:
        parohijani_qs = Parohijan.objects.none()
        svestenici_qs = Svestenik.objects.none()
        krstenja_qs = Krstenje.objects.none()
        vencanja_qs = Vencanje.objects.none()
        domacinstva_qs = Domacinstvo.objects.none()

    # Get total counts per type
    counts = {
        "parohijani": parohijani_qs.count(),
        "svestenici": svestenici_qs.count(),
        "krstenja": krstenja_qs.count(),
        "vencanja": vencanja_qs.count(),
        "domacinstva": domacinstva_qs.count(),
    }
    total = sum(counts.values())

    context = {
        "stats": {
            "parohijani": Parohijan.objects.count(),
            "krstenja": Krstenje.objects.count(),
            "vencanja": Vencanje.objects.count(),
            "svestenici": Svestenik.objects.count(),
        },
        "query": query,
        "total": total,
        "parohijani": parohijani_qs[:SEARCH_PREVIEW_LIMIT],
        "parohijani_count": counts["parohijani"],
        "svestenici": svestenici_qs[:SEARCH_PREVIEW_LIMIT],
        "svestenici_count": counts["svestenici"],
        "krstenja": krstenja_qs[:SEARCH_PREVIEW_LIMIT],
        "krstenja_count": counts["krstenja"],
        "vencanja": vencanja_qs[:SEARCH_PREVIEW_LIMIT],
        "vencanja_count": counts["vencanja"],
        "domacinstva": domacinstva_qs[:SEARCH_PREVIEW_LIMIT],
        "domacinstva_count": counts["domacinstva"],
    }

    return render(request, "registar/search_view.html", context)


def search_autocomplete(request):
    """JSON endpoint за аутокомплит претрагу — grouped by type, ranked by relevance."""
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"groups": []})

    variants = get_query_variants(query)

    def build_q(fields):
        q = Q()
        for v in variants:
            for field in fields:
                q |= Q(**{f"{field}__icontains": v})
        return q

    def rank_item(text):
        """Start-of-name matches rank 0, contains matches rank 1."""
        text_lower = text.lower()
        for v in variants:
            if text_lower.startswith(v.lower()):
                return 0
        return 1

    groups = []

    # Парохијани
    parohijani = list(
        Parohijan.objects.filter(build_q(["ime", "prezime"])).distinct()[:10]
    )
    if parohijani:
        items = sorted(
            [
                {
                    "text": f"{p.ime} {p.prezime}",
                    "sub": str(p.datum_rodjenja or ""),
                    "url": f"/parohijan/{p.uid}/",
                    "_rank": rank_item(f"{p.ime} {p.prezime}"),
                }
                for p in parohijani
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Парохијани", "items": items})

    # Свештеници
    svestenici = list(
        Svestenik.objects.filter(build_q(["ime", "prezime"])).distinct()[:10]
    )
    if svestenici:
        items = sorted(
            [
                {
                    "text": f"{s.ime} {s.prezime}",
                    "sub": s.zvanje,
                    "url": f"/svestenik/{s.uid}/",
                    "_rank": rank_item(f"{s.ime} {s.prezime}"),
                }
                for s in svestenici
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Свештеници", "items": items})

    # Крштења
    krstenja = list(
        Krstenje.objects.filter(
            build_q(["dete__ime", "otac__ime", "otac__prezime", "majka__ime"])
        )
        .select_related("dete", "otac", "majka")
        .distinct()[:10]
    )
    if krstenja:
        items = sorted(
            [
                {
                    "text": f"{k.ime_deteta} {k.prezime_oca}",
                    "sub": str(k.datum or ""),
                    "url": f"/krstenje/{k.uid}/",
                    "_rank": rank_item(k.ime_deteta or ""),
                }
                for k in krstenja
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Крштења", "items": items})

    # Венчања
    vencanja = list(
        Vencanje.objects.filter(
            build_q(
                ["zenik__ime", "zenik__prezime", "nevesta__ime", "nevesta__prezime"]
            )
        )
        .select_related("zenik", "nevesta")
        .distinct()[:10]
    )
    if vencanja:
        items = sorted(
            [
                {
                    "text": f"{v.ime_zenika} и {v.ime_neveste} {v.prezime_zenika}",
                    "sub": str(v.datum or ""),
                    "url": f"/vencanje/{v.uid}/",
                    "_rank": rank_item(v.ime_zenika or ""),
                }
                for v in vencanja
            ],
            key=lambda x: x["_rank"],
        )[:3]
        for item in items:
            del item["_rank"]
        groups.append({"label": "Венчања", "items": items})

    return JsonResponse({"groups": groups})


