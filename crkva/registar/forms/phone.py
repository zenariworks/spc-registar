"""Cyrillic-Serbian phone field with loose input parsing.

Wraps django-phonenumber-field with three UX upgrades:
1. Pre-strips common separators (spaces, dashes, parens, dots, slashes)
   so users can paste "(061) 234-5678" or "061 234 5678" naturally.
2. Replaces the English "Enter a valid phone number..." with a
   Cyrillic-Serbian message and a Serbian example.
3. Sets mobile-friendly widget attrs: type=tel triggers the phone
   keypad on mobile, autocomplete=tel lets browsers fill saved numbers.
"""

import re

from phonenumber_field.formfields import PhoneNumberField as BasePhoneNumberField

# Common separators users add naturally — phonenumberslib parses through
# most of these but errors on stray non-digits, so normalize first.
_STRIP_RE = re.compile(r"[\s\-./()]+")


class SerbianPhoneField(BasePhoneNumberField):
    """PhoneNumberField with loose parsing and Cyrillic Serbian errors."""

    default_error_messages = {
        "invalid": (
            "Унесите важећи број телефона " "(нпр. 061 234 5678 или +381 61 234 5678)."
        ),
        "required": "Ово поље је обавезно.",
    }

    def __init__(self, *args, placeholder="061 234 5678", **kwargs):
        kwargs.setdefault("region", "RS")
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
        if isinstance(value, str):
            value = _STRIP_RE.sub("", value).strip()
        return super().to_python(value)
