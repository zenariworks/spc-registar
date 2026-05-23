"""Single canonical find_or_create for Osoba records.

The previous migrations had three subtly different implementations:
  - migracija_vencanja used `ime__iexact + prezime__iexact`
  - migracija_krstenja used `ime__exact + prezime__exact` AND refresh_from_db
  - migracija_ukucana_parohijana used the shared get_or_create_osoba
This module gives all three callers one stable implementation, with an
optional in-memory cache to keep the hot loop out of the database.
"""

from __future__ import annotations

from django.db import connection

from registar.models import Osoba

# Per-tenant cache: outer key is the schema name so two tenants running
# back-to-back in the same process do not contaminate each other's lookups.
_OSOBA_CACHE_BY_SCHEMA: dict[str, dict[tuple[str, str], Osoba]] = {}


def _cache() -> dict[tuple[str, str], Osoba]:
    return _OSOBA_CACHE_BY_SCHEMA.setdefault(connection.schema_name, {})


def _key(ime: str, prezime: str) -> tuple[str, str]:
    return (ime.strip().lower(), prezime.strip().lower())


def warm_osoba_cache() -> int:
    """Prefill the cache with every existing Osoba indexed by (ime, prezime)."""
    _cache().clear()
    for osoba in Osoba.objects.all().only("uid", "ime", "prezime"):
        _cache()[_key(osoba.ime or "", osoba.prezime or "")] = osoba
    return len(_cache())


def lookup_osoba(ime: str | None, prezime: str | None) -> Osoba | None:
    """Cache-first lookup of an existing Osoba by (ime, prezime).

    Returns the cached Osoba or None. Use this BEFORE deciding whether
    to create a new row keyed on an external UID.
    """
    if not ime or not prezime:
        return None
    key = _key(ime.strip(), prezime.strip())
    return _cache().get(key)


def cache_osoba(osoba: Osoba) -> None:
    """Insert (or update) an Osoba in the in-memory cache.

    Use this after creating an Osoba via a path that bypasses
    find_or_create_osoba (e.g. raw get_or_create on a UID key) so
    subsequent lookups still find it without round-tripping the DB.
    """
    if osoba is None or not osoba.ime or not osoba.prezime:
        return
    key = _key(osoba.ime, osoba.prezime)
    _cache()[key] = osoba


def find_or_create_osoba(ime: str | None, prezime: str | None, **extra) -> Osoba | None:
    """Find an Osoba by (ime, prezime) case-insensitively, or create one.

    On match, only fills in fields that are currently None or empty —
    never overwrites an existing non-empty value. On miss, creates with
    `parohijan=False` by default (override via extra).
    """
    if not ime or not prezime:
        return None
    ime = ime.strip()
    prezime = prezime.strip()
    if not ime or not prezime:
        return None

    key = _key(ime, prezime)
    cached = _cache().get(key)
    if cached is not None:
        existing = cached
    else:
        existing = Osoba.objects.filter(
            ime__iexact=ime, prezime__iexact=prezime
        ).first()
        if existing:
            _cache()[key] = existing

    if existing:
        updates = {
            k: v for k, v in extra.items() if v and not getattr(existing, k, None)
        }
        if updates:
            Osoba.objects.filter(pk=existing.pk).update(**updates)
            existing.refresh_from_db()
            _cache()[key] = existing
        return existing

    data = {"ime": ime, "prezime": prezime, "parohijan": False}
    data.update({k: v for k, v in extra.items() if v is not None})
    created = Osoba.objects.create(**data)
    _cache()[key] = created
    return created
