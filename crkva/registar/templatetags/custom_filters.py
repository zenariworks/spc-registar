"""
Модул за дефинисање прилагођених шaблонских филтера.
"""

import re

from django import template

register = template.Library()


@register.filter
def highlight(value, search_query):
    """Истиче жутом бојом задати текст из search_query."""
    if not search_query:
        return value
    pattern = re.compile(re.escape(search_query), re.IGNORECASE)
    def replace(match):
        return f'<span style="background-color: yellow;">{match.group()}</span>'

    return pattern.sub(replace, value)
