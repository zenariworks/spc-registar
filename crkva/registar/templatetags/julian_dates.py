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


def to_julian_date_numeric(datum):
    """Нумерички јулијански запис за штампу: ``YYYY.MM.DD / DD`` када су
    грегоријански и јулијански датум у истом месецу, односно
    ``YYYY.MM.DD / YYYY.MM.DD`` када одузимање 13 дана пређе у претходни
    месец/годину (нпр. 2024.01.05 → 2023.12.23)."""
    if isinstance(datum, datetime.date):
        julijanski = gregorian_to_julian(datum)
        if (julijanski.year, julijanski.month) == (datum.year, datum.month):
            return f"{datum:%Y.%m.%d} / {julijanski.day:02d}"
        return f"{datum:%Y.%m.%d} / {julijanski:%Y.%m.%d}"
    return ""


register.filter("julian_date", to_julian_date)
register.filter("julian_date_numeric", to_julian_date_numeric)
