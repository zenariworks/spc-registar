"""Utilities set for data processing"""
from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.utils import timezone


def convert_to_date(date: str = None, format: str = "%Y%m%d"):
    """Convert string format to datetime"""

    date = date.replace("-", "")

    try:
        date = datetime.strptime(date, format)
    except ValueError:
        year = int(date[0:4])
        month = int(date[4:6])
        day = int(date[6:8])
        date = datetime(
            year, month if month != 0 else month + 1, day if day != 0 else day + 1
        )
    date = timezone.make_aware(date)

    return date


def add_timedelta(date, delta: str = None):
    """Add timedelta to datetime"""
    date = timezone.make_naive(date)

    delta_date = None
    delta = str(delta)
    if delta == "Dag":
        delta_date = date + relativedelta(days=+1)
    elif delta == "Week":
        delta_date = date + relativedelta(weeks=+1)
    elif delta == "Maand":
        delta_date = date + relativedelta(months=+1)
    elif delta == "Kwartaal":
        delta_date = date + relativedelta(months=+3)
    elif delta == "Jaar":
        delta_date = date + relativedelta(years=+1)
    elif delta == "Peildatum":
        delta_date = date

    delta_date = timezone.make_aware(delta_date)

    return delta_date
