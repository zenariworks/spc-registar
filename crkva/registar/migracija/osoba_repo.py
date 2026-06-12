"""Single canonical find_or_create for Osoba records.

The cache is keyed (ime, prezime) -> list[Osoba] (not a single Osoba) so
that callers needing safety-signal-based dedup (address/phone) can scan
every same-name candidate, not just the first one written to the cache.
"""

from __future__ import annotations

from django.db import connection
from registar.models import Osoba

# Per-tenant cache: schema -> {(ime_lower, prezime_lower): [Osoba, ...]}.
_OSOBA_CACHE_BY_SCHEMA: dict[str, dict[tuple[str, str], list[Osoba]]] = {}


def _cache() -> dict[tuple[str, str], list[Osoba]]:
    return _OSOBA_CACHE_BY_SCHEMA.setdefault(connection.schema_name, {})


def _key(ime: str, prezime: str) -> tuple[str, str]:
    return (ime.strip().lower(), prezime.strip().lower())


def warm_osoba_cache() -> int:
    """Prefill the cache with every Osoba; multiple same-name rows allowed."""
    bucket = _cache()
    bucket.clear()
    count = 0
    for osoba in Osoba.objects.all().only(
        "uid",
        "ime",
        "prezime",
        "adresa_id",
        "tel_fiksni",
        "tel_mobilni",
        "parohijan",
        "devojacko_prezime",
        "pol",
    ):
        bucket.setdefault(_key(osoba.ime or "", osoba.prezime or ""), []).append(osoba)
        count += 1
    return count


def lookup_osoba(ime: str | None, prezime: str | None) -> Osoba | None:
    """First cached Osoba with this name, or None. Kept for back-compat with
    callers that do simple name-only dedup (krstenja, vencanja). Prefer
    `lookup_all_osoba` or `find_matching_osoba` when safety signals matter.
    """
    if not ime or not prezime:
        return None
    matches = _cache().get(_key(ime, prezime))
    return matches[0] if matches else None


def lookup_all_osoba(ime: str | None, prezime: str | None) -> list[Osoba]:
    """Every cached Osoba sharing this name (caller decides which to reuse)."""
    if not ime or not prezime:
        return []
    return list(_cache().get(_key(ime, prezime), []))


def find_matching_osoba(
    ime: str | None,
    prezime: str | None,
    *,
    adresa=None,
    tel_f: str | None = None,
    tel_m: str | None = None,
) -> Osoba | None:
    """Return the first cached Osoba with this name AND a matching safety
    signal (address, fiksni, or mobilni). Returns None if no candidate
    shares any signal. Used by the parohijan/domacin import so multi-row
    name collisions still dedup correctly when some share a tel/address.
    """
    for cand in lookup_all_osoba(ime, prezime):
        if adresa is not None and cand.adresa_id == adresa.uid:
            return cand
        if tel_f and cand.tel_fiksni and str(cand.tel_fiksni) == tel_f:
            return cand
        if tel_m and cand.tel_mobilni and str(cand.tel_mobilni) == tel_m:
            return cand
    return None


def cache_osoba(osoba: Osoba | None) -> None:
    """Append an Osoba to the cache bucket for its name (idempotent on pk)."""
    if osoba is None or not osoba.ime or not osoba.prezime:
        return
    bucket = _cache().setdefault(_key(osoba.ime, osoba.prezime), [])
    if not any(o.pk == osoba.pk for o in bucket):
        bucket.append(osoba)


def find_or_create_osoba(ime: str | None, prezime: str | None, **extra) -> Osoba | None:
    """Find an Osoba by (ime, prezime) case-insensitively, or create one.

    On match (first same-name Osoba), only fills in fields that are currently
    None or empty. On miss, creates with parohijan=False by default.
    """
    if not ime or not prezime:
        return None
    ime = ime.strip()
    prezime = prezime.strip()
    if not ime or not prezime:
        return None

    existing = lookup_osoba(ime, prezime)
    if existing is None:
        existing = Osoba.objects.filter(
            ime__iexact=ime, prezime__iexact=prezime
        ).first()
        if existing:
            cache_osoba(existing)

    if existing:
        updates = {
            k: v for k, v in extra.items() if v and not getattr(existing, k, None)
        }
        if updates:
            Osoba.objects.filter(pk=existing.pk).update(**updates)
            existing.refresh_from_db()
        return existing

    data = {"ime": ime, "prezime": prezime, "parohijan": False}
    data.update({k: v for k, v in extra.items() if v is not None})
    created = Osoba.objects.create(**data)
    cache_osoba(created)
    return created
