"""
Модул за дефинисање прилагођених шaблонских филтера.
"""

import re

from django import template

register = template.Library()


@register.filter
def markiraj(value, upit):
    """Истиче жутом бојом задати текст из 'upit' аргумента."""
    if not upit:
        return value

    termini = [re.escape(termin) for termin in upit.split()]
    pattern = re.compile(r'({})'.format('|'.join(termini)), re.IGNORECASE)

    def replace(match):
        return f'<span style="background-color: peachpuff;">{match.group()}</span>'

    return pattern.sub(replace, value)
