"""Tenant-aware phone field with loose input + Cyrillic Serbian errors.

Wraps django-phonenumber-field with three UX upgrades:
1. Pre-strips common separators (spaces, dashes, parens, dots, slashes)
   so users can paste "(061) 234-5678" or "061 234 5678" naturally.
2. Replaces the English "Enter a valid phone number..." with a
   Cyrillic-Serbian message.
3. Sets mobile-friendly widget attrs: type=tel triggers the phone
   keypad on mobile, autocomplete=tel lets browsers fill saved numbers.

The default parsing region is read from the active tenant
(`connection.tenant.default_phone_region`), falling back to "RS".
That means an Amsterdam parish user can type "0612345678" and have
it parsed as Dutch (+31), while a Cukarica user typing the same digits
gets a Serbian (+381) number. Inputs that include an explicit +country
prefix always win regardless of region.
"""

import re

from django.db import connection
from phonenumber_field.formfields import PhoneNumberField as BasePhoneNumberField

_STRIP_RE = re.compile(r"[\s\-./()]+")


def get_tenant_phone_region(default: str = "RS") -> str:
    """Return current tenant's ISO region code, or `default` if none."""
    tenant = getattr(connection, "tenant", None)
    if tenant is None:
        return default
    return getattr(tenant, "default_phone_region", None) or default


class TenantPhoneField(BasePhoneNumberField):
    """PhoneNumberField with loose parsing and Cyrillic Serbian errors.

    Default region resolves from the current tenant at clean() time, so
    the same digits parse differently in Cukarica (RS) vs Amsterdam (NL).
    Inputs with an explicit +country prefix always win.
    """

    default_error_messages = {
        "invalid": (
            "Унесите важећи број телефона " "(нпр. 061 234 5678 или +381 61 234 5678)."
        ),
        "required": "Ово поље је обавезно.",
    }

    def __init__(self, *args, placeholder="061 234 5678", **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)
        self.widget.attrs.update(
            {
                "type": "tel",
                "inputmode": "tel",
                "autocomplete": "tel",
                "placeholder": placeholder,
            }
        )

    def to_python(self, value):
        # Resolve region per-call so the active tenant always wins, even if
        # the form class was imported at startup under the public schema.
        self.region = get_tenant_phone_region(default="RS")
        if isinstance(value, str):
            value = _STRIP_RE.sub("", value).strip()
        return super().to_python(value)
