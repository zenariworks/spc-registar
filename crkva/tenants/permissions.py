"""Role-based permission helpers.

Resource buckets — each constant matches one of the editable domains in
the registar app. Roles map to the set of resources they can write to:

    Админ        → all five
    Канцеларија  → osoba, domacinstvo, krstenje, vencanje
    Свештенство  → svestenik
    Преглед      → none

Superusers bypass the role check entirely. Anonymous users can never
write. All authenticated users can read.

Use the `tenant_role_required(resource)` decorator on write views and
the `can_edit_*` flags exposed by the context processor in templates.
For tenant-admin-only pages (e.g. user management), use
`tenant_admin_required` instead.
"""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from tenants.models import Role, UserMembership

OSOBA = "osoba"
DOMACINSTVO = "domacinstvo"
KRSTENJE = "krstenje"
VENCANJE = "vencanje"
SVESTENIK = "svestenik"

ALL_RESOURCES = frozenset({OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK})
KANCELARIJA_RESOURCES = frozenset({OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE})
SVESTENSTVO_RESOURCES = frozenset({SVESTENIK})

WRITE_BY_ROLE: dict[str, frozenset[str]] = {
    Role.ADMIN: ALL_RESOURCES,
    Role.KANCELARIJA: KANCELARIJA_RESOURCES,
    Role.SVESTENSTVO: SVESTENSTVO_RESOURCES,
    Role.PREGLED: frozenset(),
}


def can_edit(user, tenant, resource: str) -> bool:
    """True if `user` may write `resource` inside `tenant`."""
    if user is None or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if tenant is None:
        return False
    membership = UserMembership.objects.filter(user=user, tenant=tenant).first()
    if membership is None:
        return False
    return resource in WRITE_BY_ROLE.get(membership.role, frozenset())


def is_tenant_admin(user, tenant) -> bool:
    """True if `user` has Админ role in `tenant`, or is a superuser."""
    if user is None or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if tenant is None:
        return False
    return UserMembership.objects.filter(
        user=user, tenant=tenant, role=Role.ADMIN
    ).exists()


def tenant_role_required(resource: str):
    """Decorator: 403 if request.user can't write `resource` in request.tenant."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not can_edit(request.user, getattr(request, "tenant", None), resource):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def tenant_admin_required(view_func):
    """Decorator: 403 if request.user is not Админ in request.tenant."""

    @wraps(view_func)
    @login_required
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not is_tenant_admin(request.user, getattr(request, "tenant", None)):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped
