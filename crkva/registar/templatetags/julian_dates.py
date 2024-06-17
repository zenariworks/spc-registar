import datetime

from django import template

register = template.Library()

# Define a dictionary for month names in both Gregorian and Julian calendars
GREGORIAN_MONTHS = {
    1: "јануар",
    2: "фебруар",
    3: "март",
    4: "април",
    5: "мај",
    6: "јун",
    7: "јул",
    8: "август",
    9: "септембар",
    10: "октобар",
    11: "новембар",
    12: "децембар",
}


# Add a function to convert Gregorian date to Julian date
def gregorian_to_julian(date):
    julian_date = date - datetime.timedelta(days=13)
    return julian_date


def to_julian_date(value):
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
