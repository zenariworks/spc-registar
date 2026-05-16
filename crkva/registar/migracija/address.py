"""Adresa creation helpers shared across migrations."""

from __future__ import annotations

from registar.models import Adresa, Osoba


def split_adresa(adresa_text: str | None, mesto: str | None) -> Adresa:
    """Try to split 'Улица 4а' into ulica + broj. Returns a new Adresa."""
    if not adresa_text:
        return Adresa.objects.create(mesto=mesto or "")
    parts = adresa_text.rsplit(None, 1)
    if len(parts) == 2 and any(c.isdigit() for c in parts[1]):
        return Adresa.objects.create(
            ulica=parts[0], broj=parts[1][:10], mesto=mesto or ""
        )
    return Adresa.objects.create(ulica=adresa_text, mesto=mesto or "")


def set_adresa_if_empty(osoba: Osoba | None, adresa: Adresa | None) -> None:
    """Attach `adresa` to `osoba` only if the Osoba doesn't already have one."""
    if osoba is None or adresa is None:
        return
    if osoba.adresa_id:
        return
    Osoba.objects.filter(pk=osoba.pk).update(adresa=adresa)
