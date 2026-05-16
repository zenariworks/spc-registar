"""Session-routed tenant middleware.

Phase 1: this middleware is read-only. It looks up the current user's
active membership and stashes the Tenant on `request.tenant`. It does
NOT switch DB schemas yet — that wiring lands in Phase 2 when we plug
django-tenants in.
"""

from __future__ import annotations

from typing import Callable

from django.http import HttpRequest, HttpResponse

SESSION_TENANT_KEY = "active_tenant_id"


class SessionTenantMiddleware:
    """Resolve `request.tenant` from the session for every request.

    Resolution order:
      1. session["active_tenant_id"] — if set, look up that Tenant.
      2. The user's `is_default=True` membership.
      3. The first membership the user has.
      4. The system default Tenant.
      5. None — for anonymous requests or before any tenants exist.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.tenant = self._resolve_tenant(request)
        return self.get_response(request)

    @staticmethod
    def _resolve_tenant(request: HttpRequest):
        # Late import to avoid loading models before apps are ready.
        from tenants.models import Tenant, UserMembership

        # 1) Session override
        session_tid = (
            request.session.get(SESSION_TENANT_KEY)
            if hasattr(request, "session")
            else None
        )
        if session_tid:
            try:
                return Tenant.objects.get(pk=session_tid, is_active=True)
            except Tenant.DoesNotExist:
                request.session.pop(SESSION_TENANT_KEY, None)

        # 2/3) User's memberships
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            memberships = (
                UserMembership.objects.filter(user=user, tenant__is_active=True)
                .select_related("tenant")
                .order_by("-is_default", "created_at")
            )
            for m in memberships:
                request.session[SESSION_TENANT_KEY] = m.tenant_id
                return m.tenant

        # 4) System default
        try:
            return Tenant.objects.get(is_default=True, is_active=True)
        except Tenant.DoesNotExist:
            return None
