"""Merge duplicate records by re-pointing all FKs from loser → winner.

The functions here are extracted from the popravi_duplikate management
command so the same logic powers both the bulk CLI cleanup and the
per-record UI merge flow.

Contract:
    * merge_adrese(loser, winner) — reassigns Osoba.adresa, Domacinstvo.adresa,
      and Svestenik.adresa from loser → winner, then deletes loser. Returns
      a counts dict for the caller's confirmation message.
    * All work happens inside a single transaction.
    * Same-uid safety check prevents merging a row into itself.
"""

from __future__ import annotations

from typing import TypedDict

from django.db import transaction
from registar.models import Adresa, Domacinstvo, Osoba, Svestenik


class AdresaMergeResult(TypedDict):
    osoba: int
    domacinstvo: int
    svestenik: int


_KNOWN_ADRESA_REFERRERS = {Osoba, Domacinstvo, Svestenik}


def _check_referrer_coverage() -> None:
    """Fail fast if a new model has acquired an FK to Adresa without a
    matching update() call below. The UI promises the user that all
    references will be re-pointed, so a silent miss is unacceptable.
    """
    referrers = {
        rel.related_model
        for rel in Adresa._meta.get_fields()
        if (rel.one_to_many or rel.many_to_one or rel.many_to_many) and rel.auto_created
    }
    # Drop historical mirrors (django-simple-history) - those snapshot the
    # original row and do not need re-pointing on merge.
    referrers = {
        m for m in referrers if not m._meta.object_name.startswith("Historical")
    }
    missing = referrers - _KNOWN_ADRESA_REFERRERS
    if missing:
        names = ", ".join(sorted(m._meta.label for m in missing))
        raise RuntimeError(
            f"merge_adrese: new Adresa referrer(s) detected ({names}). "
            "Add them to the merge_adrese update list before running."
        )


def merge_adrese(loser: Adresa, winner: Adresa) -> AdresaMergeResult:
    """Re-point all FKs from loser → winner, then delete loser.

    Raises ValueError if the two are the same row.
    Raises RuntimeError if a new model has acquired an Adresa FK that
    this function does not know how to re-point.
    """
    if loser.uid == winner.uid:
        raise ValueError("Cannot merge a record into itself.")

    _check_referrer_coverage()

    with transaction.atomic():
        moved = AdresaMergeResult(
            osoba=Osoba.objects.filter(adresa=loser).update(adresa=winner),
            domacinstvo=Domacinstvo.objects.filter(adresa=loser).update(adresa=winner),
            svestenik=Svestenik.objects.filter(adresa=loser).update(adresa=winner),
        )
        loser.delete()
    return moved


def adresa_fanout(a: Adresa) -> AdresaMergeResult:
    """How many rows reference this Adresa via FK?

    Used for the merge preview so the user sees what will be re-pointed.
    """
    return AdresaMergeResult(
        osoba=Osoba.objects.filter(adresa=a).count(),
        domacinstvo=Domacinstvo.objects.filter(adresa=a).count(),
        svestenik=Svestenik.objects.filter(adresa=a).count(),
    )


def batch_adresa_fanout(adresas) -> dict:
    """Compute adresa_fanout for many addresses in 3 queries total.

    Single-address fanout fires 3 COUNTs; doing that for N addresses is
    3*N round-trips. This batched variant runs one GROUP BY per related
    model (Osoba / Domacinstvo / Svestenik) and returns a uid -> counts
    dict, so N addresses cost exactly 3 queries regardless of N.
    """
    from django.db.models import Count

    uids = [a.uid for a in adresas]
    if not uids:
        return {}

    def _grouped(model):
        rows = (
            model.objects.filter(adresa_id__in=uids)
            .values("adresa_id")
            .annotate(c=Count("uid"))
        )
        return {r["adresa_id"]: r["c"] for r in rows}

    o = _grouped(Osoba)
    d = _grouped(Domacinstvo)
    sv = _grouped(Svestenik)
    return {
        uid: AdresaMergeResult(
            osoba=o.get(uid, 0),
            domacinstvo=d.get(uid, 0),
            svestenik=sv.get(uid, 0),
        )
        for uid in uids
    }
