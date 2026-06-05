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

`can_edit`, `is_tenant_admin` and the context processor all resolve the
caller's role through a single helper, `tenant_permissions`, so a page
render costs one membership query instead of one per flag.
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


def tenant_permissions(user, tenant) -> tuple[bool, frozenset[str]]:
    """Resolve ``(is_admin, writable_resources)`` for ``user`` in ``tenant``.

    Issues at most **one** query. `UserMembership` is unique per
    ``(user, tenant)``, so a single active row fully determines the role.

    - Anonymous users / missing tenant → ``(False, frozenset())`` (no query).
    - Superusers → ``(True, ALL_RESOURCES)`` (no query; they need no row).
    - Otherwise the active membership's role decides both flags.
    """
    if user is None or not user.is_authenticated:
        return False, frozenset()
    if user.is_superuser:
        return True, ALL_RESOURCES
    if tenant is None:
        return False, frozenset()
    membership = UserMembership.objects.filter(
        user=user, tenant=tenant, is_active=True
    ).first()
    if membership is None:
        return False, frozenset()
    return membership.role == Role.ADMIN, WRITE_BY_ROLE.get(
        membership.role, frozenset()
    )


def can_edit(user, tenant, resource: str) -> bool:
    """True if `user` may write `resource` inside `tenant`."""
    _is_admin, writable = tenant_permissions(user, tenant)
    return resource in writable


def is_tenant_admin(user, tenant) -> bool:
    """True if `user` has Админ role in `tenant`, or is a superuser."""
    is_admin, _writable = tenant_permissions(user, tenant)
    return is_admin


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
