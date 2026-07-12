"""Adresa-related views: duplicate finder + merge action.

Adresa has no public detail or list page in the registar UI (addresses
sit attached to Osoba / Domacinstvo / Svestenik). The merge flow gets
its own admin-only page that surfaces exact-citation duplicate pairs
and offers a one-click merge per pair.

Routes:
  - GET  /adrese/duplikati/  → list candidate duplicate groups
  - POST /adresa/<loser_uid>/spoji/<winner_uid>/ → execute the merge
"""

from collections import defaultdict

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from registar.models import Adresa
from registar.services.merge import batch_adresa_fanout, merge_adrese
from tenants.permissions import tenant_admin_required


def _adresa_key(a: Adresa) -> tuple:
    """Normalized identity key — same heuristic as popravi_duplikate Phase 1."""
    return (
        (a.ulica or "").strip().lower(),
        (a.broj or "").strip().lower(),
        (a.broj_stana or "").strip().lower(),
        (a.mesto or "").strip().lower(),
    )


@tenant_admin_required
def duplikati_adresa(request):
    groups = defaultdict(list)
    for a in Adresa.objects.all().order_by("uid"):
        k = _adresa_key(a)
        if k == ("", "", "", ""):
            continue
        groups[k].append(a)
    # Collect every row that lives in a duplicate group, then look up all
    # fanout counts in 3 GROUP BY queries total instead of 3-per-row.
    dup_rows = [a for rows in groups.values() if len(rows) >= 2 for a in rows]
    fanouts = batch_adresa_fanout(dup_rows)
    dup_groups = []
    for k, rows in groups.items():
        if len(rows) < 2:
            continue
        decorated = [(a, fanouts[a.uid]) for a in rows]
        dup_groups.append(
            {
                "key": " / ".join(p for p in k if p),
                "rows": decorated,
            }
        )
    dup_groups.sort(key=lambda g: g["key"])
    return render(
        request,
        "registar/duplikati_adresa.html",
        {"groups": dup_groups, "total_groups": len(dup_groups)},
    )


@require_POST
@tenant_admin_required
def spoji_adresu(request, loser_uid, winner_uid):
    # The whole flow runs in one transaction with a row-level lock on both
    # rows so that two concurrent merges of the same pair cannot race -
    # without this, request A could fetch loser, get scheduled out, request B
    # could delete loser via its own merge, and request A's merge_adrese()
    # would silently re-point 0 rows then UPDATE-NOT-FOUND on the delete and
    # still flash 'success'.
    try:
        with transaction.atomic():
            loser = get_object_or_404(Adresa.objects.select_for_update(), uid=loser_uid)
            winner = get_object_or_404(
                Adresa.objects.select_for_update(), uid=winner_uid
            )
            moved = merge_adrese(loser, winner)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("duplikati_adresa")
    messages.success(
        request,
        f"Адресе спојене: пресмерено {moved['osoba']} парохијана, "
        f"{moved['domacinstvo']} домаћинстава, {moved['svestenik']} свештеника.",
    )
    return redirect("duplikati_adresa")
