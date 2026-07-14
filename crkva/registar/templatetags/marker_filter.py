"""
Модул за дефинисање прилагођених шaблонских филтера.
"""

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from registar.utils import get_query_variants

register = template.Library()


def _safe(value):
    """Ескејпуј + означи као safe тако да безбедносни уговор важи на СВАКОМ излазу.

    Шаблони користе `{{ value|markiraj:q|safe }}`; `|safe` онемогућава
    аутоескејп, па markiraj мора сам да врати већ ескејповану вредност —
    и када истиче поготке и на свим раним излазима (празан упит, без
    термина, грешка). У супротном сирова вредност из базе се рендерује
    неескејповано → складиштени XSS (#375).
    """
    return mark_safe(escape("" if value is None else str(value)))


@register.filter
def markiraj(value, upit):
    """Истиче жутом бојом задати текст из 'upit' аргумента.

    SECURITY CONTRACT
    -----------------
    This filter escapes its input via django.utils.html.escape() BEFORE
    wrapping any matches in highlight <span>s, then returns mark_safe().
    EVERY return path (including empty query / no terms / error) goes
    through escape() — see `_safe()` — so the contract is unconditional.

    Templates rely on this contract: every `{{ value|markiraj:q|safe }}`
    in the codebase trusts that user-supplied `value` cannot inject HTML,
    because markiraj has already escaped it.

    If you ever remove the `escape()` calls below, ALL callers using
    `|safe` after this filter become vulnerable to stored XSS. Search
    for `markiraj.*safe` across templates before touching this function.
    """
    if not upit:
        return _safe(value)

    # Припреми све варијанте (латиница/ћирилица) за сваки унети термин
    raw_terms = [t for t in upit.split() if t]
    all_terms = []
    for t in raw_terms:
        all_terms.extend(get_query_variants(t))
    if not all_terms:
        return _safe(value)
    termini = [re.escape(termin) for termin in set(all_terms)]
    pattern = re.compile(r"({})".format("|".join(termini)), re.IGNORECASE)

    def replace(match):
        return (
            f'<span style="background-color: peachpuff;">{escape(match.group())}</span>'
        )

    try:
        original = "" if value is None else str(value)
        escaped = escape(original)
        highlighted = pattern.sub(replace, escaped)
        return mark_safe(highlighted)
    except Exception:
        # Fallback: still escaped+safe so the contract holds on errors too.
        return _safe(value)
