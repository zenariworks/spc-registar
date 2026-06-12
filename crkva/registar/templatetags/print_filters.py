"""Филтери за штампане обрасце (крштеница/венчаница)."""

from django import template

register = template.Library()

CRTICA = "-"


@register.filter
def crtica(value):
    """Празну ћелију приказује као „-" уместо празнине или „None".

    Враћа „-" када је вредност ``None`` или празан/празнински стринг;
    у супротном враћа саму вредност (стрипован текст). Нула и сличне
    „falsy" али смислене вредности се чувају.
    """
    if value is None:
        return CRTICA
    text = str(value).strip()
    return text if text else CRTICA
