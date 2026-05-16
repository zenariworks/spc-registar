"""Session-routed tenant middleware.

Phase 2a-lite: the runtime is schema-aware via raw `SET search_path`
on the active connection. We don't depend on django-tenants' custom
DB engine yet — Phase 2b will activate that.

Resolution order for `request.tenant`:
  1. session["active_tenant_id"] — explicit override
  2. The user's `is_default=True` membership
  3. The first membership the user has
  4. The system default Tenant (Tenant.is_default=True)
  5. None — for anonymous requests or before any tenants exist

After resolution we point the connection at the tenant's schema by
running `SET search_path TO <schema>, public;` — but only if the
schema actually exists. During Phase 2a no per-tenant schemas exist
yet, so we always stay on `public` in practice. The connection is
reset to `public` at the end of every request.
"""

from __future__ import annotations

from typing import Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse

SESSION_TENANT_KEY = "active_tenant_id"


def _schema_exists(name: str) -> bool:
    """Return True if the given Postgres schema exists."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
            [name],
        )
        return cur.fetchone() is not None


def _set_search_path(schema_name: str | None) -> None:
    """Point the current connection at `<schema_name>, public` or just `public`."""
    with connection.cursor() as cur:
        if schema_name:
            # Quote the identifier defensively. schema_name is validated by
            # django-tenants' _check_schema_name validator at save() time, so
            # it's already restricted to [a-z_][a-z0-9_]*, but parameter
            # binding here protects against future loosening.
            cur.execute("SET search_path TO %s, public", [schema_name])
        else:
            cur.execute("SET search_path TO public")


class SessionTenantMiddleware:
    """Resolve `request.tenant`, then switch the connection's search_path."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        tenant = self._resolve_tenant(request)
        request.tenant = tenant
        self._activate_tenant_schema(tenant)
        try:
            return self.get_response(request)
        finally:
            _set_search_path(None)

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

    @staticmethod
    def _activate_tenant_schema(tenant) -> None:
        """Activate the tenant's schema if it exists; otherwise stay on public.

        Phase 2a: tenant schemas don't exist yet, so this always falls back
        to public. Phase 2b will create the schemas and the search_path
        switch will then actually point the DB at per-tenant data.
        """
        if tenant is None or not tenant.schema_name:
            _set_search_path(None)
            return
        try:
            if _schema_exists(tenant.schema_name):
                _set_search_path(tenant.schema_name)
            else:
                _set_search_path(None)
        except Exception:  # pylint: disable=broad-except
            # Defensive: never let middleware kill the request.
            _set_search_path(None)
