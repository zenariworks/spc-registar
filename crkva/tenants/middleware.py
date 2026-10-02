"""Middleware који бира парохију (tenant) из сесије (фаза 2b: django-tenants активан).

Одређује `request.tenant` из сесије, чланства или подразумеване парохије, па
тражи од django-tenants омотача везе да пребаци шему. По завршетку враћа шему
која је била активна *пре* захтева, тако да веза сваки захтев завршава у
предвидивом стању — и да тест клијенти у тесту који је већ поставио парохију
задрже ту парохију.
"""

# pylint: disable=import-outside-toplevel

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse
from django_tenants.utils import schema_exists
from tenants.permissions import prime_tenant_permissions

if TYPE_CHECKING:
    from tenants.models import Clanstvo, Zakupac

SESSION_TENANT_KEY = "active_tenant_id"
logger = logging.getLogger(__name__)


def _korisnik(request: HttpRequest):
    """Пријављени корисник захтева, или None за анонимног."""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user
    return None


def _aktivno_clanstvo(user, tenant):
    """Једино активно чланство корисника у парохији, или None.

    Деактивирано чланство закључава корисника само из те парохије — никад из
    других, и никад не дира заједнички User.is_active.
    """
    from tenants.models import Clanstvo

    if user is None:
        return None
    return Clanstvo.objects.filter(
        korisnik=user, parohija=tenant, is_active=True
    ).first()


def _iz_sesije(request: HttpRequest, user) -> tuple[Zakupac, Clanstvo | None] | None:
    """Парохија запамћена у сесији, ако је активна и корисник сме у њу.

    Суперкорисник улази у било коју парохију без чланства. Неактивна или
    недоступна парохија се избацује из сесије; тада враћа None.
    """
    from tenants.models import Zakupac

    session = getattr(request, "session", None)
    if session is None:
        return None
    session_tid = session.get(SESSION_TENANT_KEY)
    if not session_tid:
        return None
    try:
        tenant = Zakupac.objects.get(pk=session_tid, is_active=True)
    except Zakupac.DoesNotExist:
        session.pop(SESSION_TENANT_KEY, None)
        return None
    if user is not None and user.is_superuser:
        return tenant, None
    membership = _aktivno_clanstvo(user, tenant)
    if membership is not None:
        return tenant, membership
    session.pop(SESSION_TENANT_KEY, None)
    return None


def _iz_clanstva(request: HttpRequest, user) -> tuple[Zakupac, Clanstvo | None] | None:
    """Парохија првог активног чланства (подразумевано, па најстарије).

    Изабрана парохија се памти у сесији; без чланства враћа None.
    """
    from tenants.models import Clanstvo

    membership = (
        Clanstvo.objects.filter(korisnik=user, parohija__is_active=True, is_active=True)
        .select_related("parohija")
        .order_by("-is_default", "created_at")
        .first()
    )
    if membership is None:
        return None
    request.session[SESSION_TENANT_KEY] = membership.parohija_id
    return membership.parohija, membership


def _podrazumevana() -> tuple[Zakupac | None, None]:
    """Подразумевана парохија, без чланства; ``(None, None)`` ако је нема.

    Пријављени корисник који стигне довде нема активно чланство нигде, па (с
    правом) нема ни овлашћења у њој.
    """
    from tenants.models import Zakupac

    try:
        return Zakupac.objects.get(is_default=True, is_active=True), None
    except Zakupac.DoesNotExist:
        return None, None


class SessionTenantMiddleware:
    """Одређује request.tenant из сесије и пребацује шему базе."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Поставља парохију за захтев и враћа претходну шему после њега.

        Чланство учитано за избор шеме одређује и овлашћења корисника; њиме се
        пуни кеш за захтев, па га context processor и can_edit/is_tenant_admin
        користе уместо новог упита (#256).
        """
        prior_tenant = getattr(connection, "tenant", None)
        tenant, membership = self._resolve_tenant(request)
        request.tenant = tenant
        prime_tenant_permissions(getattr(request, "user", None), tenant, membership)
        self._activate(tenant)
        try:
            return self.get_response(request)
        finally:
            self._restore(prior_tenant)

    @staticmethod
    def _resolve_tenant(request: HttpRequest) -> tuple[Zakupac | None, Clanstvo | None]:
        """Враћа ``(tenant, membership)``: сесија, па чланство, па подразумевана.

        ``membership`` је активни ``Clanstvo`` позиваоца у изабраној парохији
        кад је познат (да би позивалац напунио кеш овлашћења), или ``None`` за
        суперкориснике (ред није потребан), анонимне кориснике или кад корисник
        нема активно чланство у изабраној парохији.
        """
        user = _korisnik(request)
        izbor = _iz_sesije(request, user)
        if izbor is not None:
            return izbor
        if user is not None:
            izbor = _iz_clanstva(request, user)
            if izbor is not None:
                return izbor
        return _podrazumevana()

    @staticmethod
    def _activate(tenant) -> None:
        """Пребацује на шему парохије; без парохије или шеме остаје public."""
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
        """Враћа шему која је била активна пре захтева."""
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
