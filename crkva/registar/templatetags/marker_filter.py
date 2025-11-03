"""
Модул за дефинисање прилагођених шaблонских филтера.
"""

import re
from django.utils.safestring import mark_safe
from registar.utils import get_query_variants

from django import template

register = template.Library()


@register.filter
def markiraj(value, upit):
    """Истиче жутом бојом задати текст из 'upit' аргумента."""
    if not upit:
        return value

    # Припреми све варијанте (латиница/ћирилица) за сваки унети термин
    raw_terms = [t for t in upit.split() if t]
    all_terms = []
    for t in raw_terms:
        all_terms.extend(get_query_variants(t))
    if not all_terms:
        return value
    termini = [re.escape(termin) for termin in set(all_terms)]
    pattern = re.compile(r'({})'.format('|'.join(termini)), re.IGNORECASE)

    def replace(match):
        return f'<span style="background-color: peachpuff;">{match.group()}</span>'

    try:
        original = "" if value is None else str(value)
        highlighted = pattern.sub(replace, original)
        return mark_safe(highlighted)
    except Exception:
        # Fallback to original value on any error
        return value
