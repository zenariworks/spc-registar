"""Template filters for phone number formatting and linking."""

import phonenumbers
from django import template
from phonenumbers import NumberParseException

register = template.Library()


@register.filter
def format_phone(phone_str):
    """Format phone number for display.

    Args:
        phone_str: Phone number string or PhoneNumber object

    Returns:
        Formatted phone number string
    """
    if not phone_str:
        return ""

    # Handle PhoneNumber objects from phonenumber_field
    if hasattr(phone_str, "as_national"):
        return phone_str.as_national

    # Handle string inputs
    try:
        phone = phonenumbers.parse(str(phone_str), "RS")
        return phonenumbers.format_number(
            phone, phonenumbers.PhoneNumberFormat.NATIONAL
        )
    except (NumberParseException, AttributeError):
        return str(phone_str)


@register.filter
def tel_link(phone_str):
    """Generate tel: URI for phone number.

    Args:
        phone_str: Phone number string or PhoneNumber object

    Returns:
        International format suitable for tel: links
    """
    if not phone_str:
        return ""

    # Handle PhoneNumber objects from phonenumber_field
    if hasattr(phone_str, "as_e164"):
        return phone_str.as_e164 or ""

    # Handle string inputs
    try:
        phone = phonenumbers.parse(str(phone_str), "RS")
        return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
    except (NumberParseException, AttributeError):
        # Fallback: try to clean and return
        cleaned = "".join(filter(str.isdigit, str(phone_str)))
        if cleaned:
            if cleaned.startswith("381"):
                return f"+{cleaned}"
            elif cleaned.startswith("0"):
                return f"+381{cleaned[1:]}"
            else:
                return f"+381{cleaned}"
        return ""


@register.filter
def phone_icon(phone_str):
    """Get appropriate icon for phone type.

    Args:
        phone_str: Phone number string or PhoneNumber object

    Returns:
        Font Awesome icon class name
    """
    if not phone_str:
        return "fa-phone"

    # Convert to string for parsing
    phone_string = str(phone_str)

    try:
        phone = phonenumbers.parse(phone_string, "RS")
        number_type = phonenumbers.number_type(phone)

        if number_type in [
            phonenumbers.PhoneNumberType.MOBILE,
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE,
        ]:
            return "fa-mobile-screen"
        elif number_type == phonenumbers.PhoneNumberType.FIXED_LINE:
            return "fa-phone"
        else:
            return "fa-phone"
    except (NumberParseException, AttributeError):
        # Fallback heuristic: check if number starts with 06 (Serbian mobile prefix)
        cleaned = "".join(filter(str.isdigit, phone_string))
        if cleaned.startswith("06") or cleaned.startswith("3816"):
            return "fa-mobile-screen"
        return "fa-phone"
