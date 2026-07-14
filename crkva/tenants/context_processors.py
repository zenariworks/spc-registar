"""Expose tenant + per-resource write flags to every template."""

from __future__ import annotations

from tenants.permissions import (
    DOMACINSTVO,
    KRSTENJE,
    OSOBA,
    SVESTENIK,
    VENCANJE,
    tenant_permissions,
)


def current_tenant(request):
    """Make request.tenant, can_edit_<resource>, and is_admin available.

    Templates may use either `tenant`/`is_tenant_admin` (django-tenants
    schema-level naming) or the user-facing aliases `parohija`/
    `is_parohija_admin` interchangeably.

    The role is resolved once (a single membership query) and every flag is
    derived from it in memory, so a render costs one query rather than six.
    """
    parohija = getattr(request, "tenant", None)
    korisnik = getattr(request, "user", None)
    is_admin, writable = tenant_permissions(korisnik, parohija)
    return {
        # django-tenants infrastructure naming (kept for backwards compat)
        "tenant": parohija,
        "is_tenant_admin": is_admin,
        # User-facing aliases — preferred in new templates.
        "parohija": parohija,
        "is_parohija_admin": is_admin,
        "can_edit_osoba": OSOBA in writable,
        "can_edit_domacinstvo": DOMACINSTVO in writable,
        "can_edit_krstenje": KRSTENJE in writable,
        "can_edit_vencanje": VENCANJE in writable,
        "can_edit_svestenik": SVESTENIK in writable,
    }
