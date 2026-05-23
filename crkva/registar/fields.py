"""Custom model fields used across registar.

TenantPhoneNumberField — model-level counterpart of TenantPhoneField (form).
Resolves the parsing region from the active tenant
(`connection.tenant.default_phone_region`) at value-coerce time.

Why this matters: `Osoba.objects.create(tel_mobilni='0612345678')` goes
through the model field's descriptor, NOT the form field. Without this,
the DBF importer (importuj_dbf, migracija_*) would silently parse Dutch
local numbers as Serbian and store wrong +E164 prefixes.

Falls back to the explicit `region=` constructor kwarg, then to "RS",
when no tenant is active (e.g. under public schema during makemigrations).
"""

from django.db import connection
from phonenumber_field.modelfields import PhoneNumberField as BasePhoneNumberField


class TenantPhoneNumberField(BasePhoneNumberField):
    @property
    def region(self):
        tenant = getattr(connection, "tenant", None)
        if tenant is not None:
            r = getattr(tenant, "default_phone_region", None)
            if r:
                return r
        return self._region or "RS"
