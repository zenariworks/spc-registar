"""Tenant context manager for seed_* commands.

Wraps the boilerplate of switching connection.tenant + restoring it on
exit. All seed_* commands use this.
"""

from __future__ import annotations

from contextlib import contextmanager

from django.core.management.base import CommandError
from django.db import connection
from django_tenants.utils import schema_exists
from tenants.models import Zakupac


@contextmanager
def with_tenant(shema: str):
    """Set connection.tenant for the duration of the with-block."""
    if not schema_exists(shema):
        raise CommandError(
            f"Schema {shema!r} не постоји. Доступни: "
            f"{', '.join(t.schema_name for t in Zakupac.objects.all())}"
        )
    parohija = Zakupac.objects.get(schema_name=shema)
    prior = getattr(connection, "tenant", None)
    connection.set_tenant(parohija)
    try:
        yield parohija
    finally:
        if prior is not None:
            connection.set_tenant(prior)
        else:
            connection.set_schema_to_public()
