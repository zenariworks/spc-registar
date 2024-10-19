"""
Модул филтера за конверзију грегоријанских датума у јулијанске
који се користи у Ђанго шаблонима.
"""

import datetime

from django import template
from registar.utils import GREGORIAN_MONTHS

register = template.Library()


def gregorian_to_julian(date):
    """
    Конверзија грегоријанског датума у јулијански.

    :param date: грегоријански датум
    :type date: datetime.date
    :return: јулијански датум
    :rtype: datetime.date
    """
    julian_date = date - datetime.timedelta(days=13)
    return julian_date


def to_julian_date(datum):
    """
    Конверзија датума у јулијански.

    :param datum: датум за конверзију
    :type datum: datetime.date
    :return: датум у формату "година, месец дан. (јулијански дан.)"
    :rtype: str
    """
    if isinstance(datum, datetime.date):
        gregorijanski_mesec = GREGORIAN_MONTHS[datum.month]
        julijanski_datum = gregorian_to_julian(datum)
        julianski_mesec = GREGORIAN_MONTHS[julijanski_datum.month]

        if gregorijanski_mesec == julianski_mesec:
            return f"{datum.year}, {gregorijanski_mesec} {datum.day}. ({julijanski_datum.day}.)"
        else:
            return f"{datum.year}, {gregorijanski_mesec} {datum.day}. ({julianski_mesec} {julijanski_datum.day}.)"
    return ""


register.filter("julian_date", to_julian_date)
