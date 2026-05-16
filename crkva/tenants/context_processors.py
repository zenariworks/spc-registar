"""Expose tenant + per-resource write flags to every template."""

from __future__ import annotations

from tenants.permissions import (
    DOMACINSTVO,
    KRSTENJE,
    OSOBA,
    SVESTENIK,
    VENCANJE,
    can_edit,
)


def current_tenant(request):
    """Make request.tenant and a `can_edit_<resource>` flag available."""
    tenant = getattr(request, "tenant", None)
    user = getattr(request, "user", None)
    return {
        "tenant": tenant,
        "can_edit_osoba": can_edit(user, tenant, OSOBA),
        "can_edit_domacinstvo": can_edit(user, tenant, DOMACINSTVO),
        "can_edit_krstenje": can_edit(user, tenant, KRSTENJE),
        "can_edit_vencanje": can_edit(user, tenant, VENCANJE),
        "can_edit_svestenik": can_edit(user, tenant, SVESTENIK),
    }
