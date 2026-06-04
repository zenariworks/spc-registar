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
    """Текстуални јулијански запис за штампу.

    - исти месец:      ``2022, октобар 10 / 27``
    - различит месец:  ``2022, октобар 10 / септембар 27``
    - прелаз у другу годину: ``2024, јануар 7 / 2023, децембар 25``
      — година се понавља само када се грегоријанска и
      јулијанска година разликују.
    """
    if not isinstance(datum, datetime.date):
        return ""
    julijanski = gregorian_to_julian(datum)
    gregorijanski = f"{datum.year}, {MESECI[datum.month]} {datum.day}"
    if datum.year != julijanski.year:
        jul = f"{julijanski.year}, {MESECI[julijanski.month]} {julijanski.day}"
    elif datum.month != julijanski.month:
        jul = f"{MESECI[julijanski.month]} {julijanski.day}"
    else:
        jul = f"{julijanski.day}"
    return f"{gregorijanski} / {jul}"


register.filter("julian_date", to_julian_date)
