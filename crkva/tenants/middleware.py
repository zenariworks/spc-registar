"""Session-routed tenant middleware (Phase 2b: django-tenants engine active).

Resolves `request.tenant` from session/membership/default, then asks the
django-tenants connection wrapper to switch schemas. Restores whatever
schema was active *before* the request when finished, so the connection
ends each request in a predictable state — and so test clients running
inside a test that already set a tenant see their tenant preserved.
"""

from __future__ import annotations

import logging
from typing import Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse
from django_tenants.utils import schema_exists
from tenants.permissions import prime_tenant_permissions

SESSION_TENANT_KEY = "active_tenant_id"
logger = logging.getLogger(__name__)


class SessionTenantMiddleware:
    """Resolve request.tenant from the session and switch the DB schema."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        prior_tenant = getattr(connection, "tenant", None)
        tenant, membership = self._resolve_tenant(request)
        request.tenant = tenant
        # The membership loaded to route the schema also determines the user's
        # permissions; seed the per-request cache so the context processor and
        # can_edit/is_tenant_admin reuse it instead of re-querying (#256).
        prime_tenant_permissions(getattr(request, "user", None), tenant, membership)
        self._activate(tenant)
        try:
            return self.get_response(request)
        finally:
            self._restore(prior_tenant)

    @staticmethod
    def _resolve_tenant(request: HttpRequest):
        """Return ``(tenant, membership)``.

        ``membership`` is the caller's active ``UserMembership`` in the resolved
        tenant when known (so callers can prime the permission cache), or
        ``None`` for superusers (no row needed), anonymous users, or when the
        user has no active membership in the resolved tenant.
        """
        from tenants.models import Tenant, UserMembership

        user = getattr(request, "user", None)
        is_authenticated = user is not None and user.is_authenticated
        is_superuser = is_authenticated and user.is_superuser

        def _membership(tenant):
            # The single active membership for (user, tenant), or None. A
            # deactivated membership locks the user out of this parish only —
            # never others, and never the shared User.is_active flag.
            if not is_authenticated:
                return None
            return UserMembership.objects.filter(
                user=user, tenant=tenant, is_active=True
            ).first()

        session_tid = (
            request.session.get(SESSION_TENANT_KEY)
            if hasattr(request, "session")
            else None
        )
        if session_tid:
            try:
                tenant = Tenant.objects.get(pk=session_tid, is_active=True)
            except Tenant.DoesNotExist:
                request.session.pop(SESSION_TENANT_KEY, None)
            else:
                # Superusers may enter any parish without a membership row.
                if is_superuser:
                    return tenant, None
                membership = _membership(tenant)
                if membership is not None:
                    return tenant, membership
                request.session.pop(SESSION_TENANT_KEY, None)

        if is_authenticated:
            membership = (
                UserMembership.objects.filter(
                    user=user, tenant__is_active=True, is_active=True
                )
                .select_related("tenant")
                .order_by("-is_default", "created_at")
                .first()
            )
            if membership is not None:
                request.session[SESSION_TENANT_KEY] = membership.tenant_id
                return membership.tenant, membership

        # Fallback: the default parish. An authenticated user reaching here has
        # no active membership anywhere, so (correctly) no permissions in it.
        try:
            return Tenant.objects.get(is_default=True, is_active=True), None
        except Tenant.DoesNotExist:
            return None, None

    @staticmethod
    def _activate(tenant) -> None:
        if tenant is None or not tenant.schema_name:
            connection.set_schema_to_public()
            return
        try:
            if schema_exists(tenant.schema_name):
                connection.set_tenant(tenant)
            else:
                logger.warning(
                    "tenant schema missing for %s (id=%s); falling back to public",
                    tenant.schema_name,
                    getattr(tenant, "pk", None),
                )
                connection.set_schema_to_public()
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "tenant activation failed for %s (id=%s); falling back to public",
                tenant.schema_name,
                getattr(tenant, "pk", None),
            )
            connection.set_schema_to_public()

    @staticmethod
    def _restore(prior_tenant) -> None:
        try:
            if prior_tenant is not None and getattr(prior_tenant, "schema_name", None):
                connection.set_tenant(prior_tenant)
            else:
                connection.set_schema_to_public()
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "tenant restore failed for %s; falling back to public",
                getattr(prior_tenant, "schema_name", None),
            )
            connection.set_schema_to_public()
