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
    pattern = re.escape(search_query)
    highlighted = re.sub(
        pattern,
        f'<span style="background-color: yellow;">{search_query}</span>',
        value,
        flags=re.IGNORECASE,
    )
    return highlighted
