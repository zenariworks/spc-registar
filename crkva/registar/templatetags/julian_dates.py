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
        gregorian_month = GREGORIAN_MONTHS[datum.month]
        julian_date = gregorian_to_julian(datum)
        julian_month = GREGORIAN_MONTHS[julian_date.month]

        if gregorian_month == julian_month:
            return f"{datum.year}, {gregorian_month} {datum.day}. ({julian_date.day}.)"
        else:
            return f"{datum.year}, {gregorian_month} {datum.day}. ({julian_month} {julian_date.day}.)"
    return ""


register.filter("julian_date", to_julian_date)
