"""Adresa creation helpers shared across migrations.

Adresa rows are deduplicated by the normalized 4-tuple
``(ulica, broj, broj_stana, mesto)``. The module-level cache turns the
hot loop into dict lookups; warm it once at the start of an import to
avoid an N×1 DB query pattern.
"""

from __future__ import annotations

from django.db import connection
from registar.models import Adresa, Osoba

# Per-tenant cache: outer key is the schema name so two tenants running
# back-to-back in the same process do not contaminate each other's lookups.
_ADRESA_CACHE_BY_SCHEMA: dict[str, dict[tuple[str, str, str, str], Adresa]] = {}


def _cache() -> dict[tuple[str, str, str, str], Adresa]:
    return _ADRESA_CACHE_BY_SCHEMA.setdefault(connection.schema_name, {})


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def _key(
    ulica: str | None,
    broj: str | None,
    broj_stana: str | None,
    mesto: str | None,
) -> tuple[str, str, str, str]:
    return (_norm(ulica), _norm(broj), _norm(broj_stana), _norm(mesto))


def warm_adresa_cache() -> int:
    """Prefill the cache with every existing Adresa row."""
    _cache().clear()
    for adresa in Adresa.objects.all():
        _cache()[_key(adresa.ulica, adresa.broj, adresa.broj_stana, adresa.mesto)] = (
            adresa
        )
    return len(_cache())


def nadji_dodaj_adresu(
    ulica: str | None = None,
    broj: str | None = None,
    broj_stana: str | None = None,
    mesto: str | None = None,
    **extra,
) -> Adresa:
    """Return an Adresa matching the four normalized fields, creating if absent."""
    key = _key(ulica, broj, broj_stana, mesto)
    cached = _cache().get(key)
    if cached is not None:
        return cached
    existing = Adresa.objects.filter(
        ulica__iexact=ulica or "",
        broj__iexact=broj or "",
        broj_stana__iexact=broj_stana or "",
        mesto__iexact=mesto or "",
    ).first()
    if existing:
        _cache()[key] = existing
        return existing
    created = Adresa.objects.create(
        ulica=ulica or "",
        broj=(broj or "")[:20],
        broj_stana=broj_stana or "",
        mesto=mesto or "",
        **extra,
    )
    _cache()[key] = created
    return created


def rasclani_adresu(adresa_text: str | None, mesto: str | None) -> Adresa:
    """Split 'Улица 4а' into ulica + broj and dedupe through ``find_or_create_adresa``."""
    if not adresa_text:
        return nadji_dodaj_adresu(mesto=mesto)
    parts = adresa_text.rsplit(None, 1)
    if len(parts) == 2 and any(c.isdigit() for c in parts[1]):
        return nadji_dodaj_adresu(ulica=parts[0], broj=parts[1][:20], mesto=mesto)
    return nadji_dodaj_adresu(ulica=adresa_text, mesto=mesto)


def dodaj_adresu(osoba: Osoba | None, adresa: Adresa | None) -> None:
    """Attach `adresa` to `osoba` only if the Osoba doesn't already have one."""
    if osoba is None or adresa is None:
        return
    if osoba.adresa_id:
        return
    Osoba.objects.filter(pk=osoba.pk).update(adresa=adresa)
