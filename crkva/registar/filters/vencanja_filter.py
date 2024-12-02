"""
Модул за дефинисање филтера за венчања у бази података.
"""

import django_filters
from django.db import models
from registar.models import Vencanje


class VencanjeFilter(django_filters.FilterSet):
    """Филтер за претрагу венчања на основу различитих поља."""

    search = django_filters.CharFilter(method="filter_search", label="Претрага")

    class Meta:
        model = Vencanje
        fields = []

    def filter_search(self, queryset, name, value):
        """Претражује уносе на основу више текстуалних поља."""
        return queryset.filter(
            models.Q(ime_zenika__icontains=value)
            | models.Q(prezime_zenika__icontains=value)
            | models.Q(ime_neveste__icontains=value)
            | models.Q(prezime_neveste__icontains=value)
            | models.Q(kum__icontains=value)
            | models.Q(stari_svat__icontains=value)
            | models.Q(hram__naziv__icontains=value)
        )
