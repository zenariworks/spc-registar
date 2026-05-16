"""Single canonical find_or_create for Osoba records.

The previous migrations had three subtly different implementations:
  - migracija_vencanja used `ime__iexact + prezime__iexact`
  - migracija_krstenja used `ime__exact + prezime__exact` AND refresh_from_db
  - migracija_ukucana_parohijana used the shared get_or_create_osoba
This module gives all three callers one stable implementation.
"""

from __future__ import annotations

from registar.models import Osoba


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

    existing = Osoba.objects.filter(ime__iexact=ime, prezime__iexact=prezime).first()
    if existing:
        updates = {
            k: v for k, v in extra.items() if v and not getattr(existing, k, None)
        }
        if updates:
            Osoba.objects.filter(pk=existing.pk).update(**updates)
            # Refresh so callers see the new values
            existing.refresh_from_db()
        return existing

    data = {"ime": ime, "prezime": prezime, "parohijan": False}
    data.update({k: v for k, v in extra.items() if v is not None})
    return Osoba.objects.create(**data)
