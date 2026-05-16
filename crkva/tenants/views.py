"""Tenant switching view.

A logged-in user POSTs to /tenant/switch/<id>/ and the active tenant is
swapped on their session. Superusers can pick any active tenant; regular
users only the ones they have a UserMembership for.
"""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from tenants.middleware import SESSION_TENANT_KEY
from tenants.models import Tenant, UserMembership


@login_required
@require_POST
def switch_tenant(request: HttpRequest, tenant_id: int) -> HttpResponse:
    """Set the active tenant on the session, then redirect back."""
    tenant = get_object_or_404(Tenant, pk=tenant_id, is_active=True)

    if not request.user.is_superuser:
        allowed = UserMembership.objects.filter(
            user=request.user, tenant=tenant
        ).exists()
        if not allowed:
            return HttpResponse(status=403)

    request.session[SESSION_TENANT_KEY] = tenant.pk

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if not next_url:
        next_url = reverse("pocetna")
    return HttpResponseRedirect(next_url)
