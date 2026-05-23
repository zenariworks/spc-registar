"""Session-routed tenant middleware (Phase 2b: django-tenants engine active).

Resolves `request.tenant` from session/membership/default, then asks the
django-tenants connection wrapper to switch schemas. Restores whatever
schema was active *before* the request when finished, so the connection
ends each request in a predictable state — and so test clients running
inside a test that already set a tenant see their tenant preserved.
"""

from __future__ import annotations

from typing import Callable

import logging

from django.db import connection
from django.http import HttpRequest, HttpResponse
from django_tenants.utils import schema_exists

SESSION_TENANT_KEY = "active_tenant_id"
logger = logging.getLogger(__name__)


class SessionTenantMiddleware:
    """Resolve request.tenant from the session and switch the DB schema."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        prior_tenant = getattr(connection, "tenant", None)
        tenant = self._resolve_tenant(request)
        request.tenant = tenant
        self._activate(tenant)
        try:
            return self.get_response(request)
        finally:
            self._restore(prior_tenant)

    @staticmethod
    def _resolve_tenant(request: HttpRequest):
        from tenants.models import Tenant, UserMembership

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

        try:
            return Tenant.objects.get(is_default=True, is_active=True)
        except Tenant.DoesNotExist:
            return None

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
                    tenant.schema_name, getattr(tenant, "pk", None),
                )
                connection.set_schema_to_public()
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "tenant activation failed for %s (id=%s); falling back to public",
                tenant.schema_name, getattr(tenant, "pk", None),
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
