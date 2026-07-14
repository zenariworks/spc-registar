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
from tenants.models import Clanstvo, Uloga

OSOBA = "osoba"
DOMACINSTVO = "domacinstvo"
KRSTENJE = "krstenje"
VENCANJE = "vencanje"
SVESTENIK = "svestenik"

ALL_RESOURCES = frozenset({OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE, SVESTENIK})
KANCELARIJA_RESOURCES = frozenset({OSOBA, DOMACINSTVO, KRSTENJE, VENCANJE})
SVESTENSTVO_RESOURCES = frozenset({SVESTENIK})

WRITE_BY_ROLE: dict[str, frozenset[str]] = {
    Uloga.ADMIN: ALL_RESOURCES,
    Uloga.KANCELARIJA: KANCELARIJA_RESOURCES,
    Uloga.SVESTENSTVO: SVESTENSTVO_RESOURCES,
    Uloga.PREGLED: frozenset(),
}


def _perms_from_membership(membership) -> tuple[bool, frozenset[str]]:
    """Derive ``(is_admin, writable_resources)`` from a membership row."""
    if membership is None:
        return False, frozenset()
    return membership.uloga == Uloga.ADMIN, WRITE_BY_ROLE.get(
        membership.uloga, frozenset()
    )


def _perm_cache(user) -> dict:
    """Per-request cache of resolved permissions, keyed by tenant pk.

    Stored on the ``user`` instance — within a single request the same user
    object flows through middleware, decorators and the context processor, so
    one resolution is reused everywhere. A fresh request gets a fresh user
    instance from the auth middleware, so the cache never goes stale.
    """
    cache = getattr(user, "_tenant_perms_cache", None)
    if cache is None:
        cache = {}
        user._tenant_perms_cache = cache
    return cache


def prime_tenant_permissions(user, tenant, membership) -> None:
    """Seed the per-request cache from a membership the caller already fetched.

    Called by ``SessionTenantMiddleware`` after it resolves ``request.tenant``
    (it loads the membership to route the schema anyway), so the context
    processor and ``can_edit``/``is_tenant_admin`` reuse that single lookup
    instead of re-querying. No-op for anonymous/superuser/missing tenant —
    those need no query. ``membership`` may be ``None`` (user has no active
    membership in ``tenant``), which correctly caches "no permissions".
    """
    if user is None or not user.is_authenticated or user.is_superuser:
        return
    if tenant is None:
        return
    _perm_cache(user)[tenant.pk] = _perms_from_membership(membership)


def tenant_permissions(user, tenant) -> tuple[bool, frozenset[str]]:
    """Resolve ``(is_admin, writable_resources)`` for ``user`` in ``tenant``.

    Issues at most **one** query per ``(user, tenant)`` per request, and zero
    when the middleware has already primed the cache (see
    ``prime_tenant_permissions``). `Clanstvo` is unique per
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
    cache = _perm_cache(user)
    if tenant.pk in cache:
        return cache[tenant.pk]
    membership = Clanstvo.objects.filter(
        korisnik=user, parohija=tenant, is_active=True
    ).first()
    result = _perms_from_membership(membership)
    cache[tenant.pk] = result
    return result


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
