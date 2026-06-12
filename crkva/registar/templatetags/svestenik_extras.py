"""Template tags за свештеничке податке у модалима."""

from django import template
from registar.models.svestenik import zvanja as ZVANJA

register = template.Library()


@register.simple_tag
def svestenik_zvanja():
    """Враћа листу (value, label) звања свештеника за dropdown у модалу.

    Извор је сам модел (`Svestenik.zvanje.choices`), да се листа не дуплира
    у шаблону и не одступа од модела.
    """
    return ZVANJA
