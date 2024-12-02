"""
Модул филтера за конверзију грегоријанских датума у јулијанске.
"""

import datetime

from django import template
from registar.utils import MESECI

register = template.Library()


def gregorian_to_julian(datum):
    """Конверзија грегоријанског датума у јулијански."""
    julianski_datum = datum - datetime.timedelta(days=13)
    return julianski_datum


def to_julian_date(datum):
    """Конверзија датума у јулијански."""
    if isinstance(datum, datetime.date):
        gregorijanski_mesec = MESECI[datum.month]
        julijanski_datum = gregorian_to_julian(datum)
        julianski_mesec = MESECI[julijanski_datum.month]

        if gregorijanski_mesec == julianski_mesec:
            return f"{datum.year}, {gregorijanski_mesec} {datum.day} / {julijanski_datum.day}"
        else:
            return f"{datum.year}, {gregorijanski_mesec} {datum.day} / {julianski_mesec} {julijanski_datum.day}"
    return ""


register.filter("julian_date", to_julian_date)
