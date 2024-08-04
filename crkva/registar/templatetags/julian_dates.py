import datetime

from django import template

from crkva.registar.utils import GREGORIAN_MONTHS

register = template.Library()


# Add a function to convert Gregorian date to Julian date
def gregorian_to_julian(date):
    """Конверзија грегоријанског датума у јулијански."""
    julian_date = date - datetime.timedelta(days=13)
    return julian_date


def to_julian_date(value):
    """Конверзија датума у јулијански."""
    if isinstance(value, datetime.date):
        gregorian_month = GREGORIAN_MONTHS[value.month]
        julian_date = gregorian_to_julian(value)
        julian_month = GREGORIAN_MONTHS[julian_date.month]

        if gregorian_month == julian_month:
            return f"{value.year}, {gregorian_month} {value.day}. ({julian_date.day}.)"
        else:
            return f"{value.year}, {gregorian_month} {value.day}. ({julian_month} {julian_date.day}.)"
    return ""


register.filter("julian_date", to_julian_date)
