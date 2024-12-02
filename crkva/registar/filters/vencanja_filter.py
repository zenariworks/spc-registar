"""
Модул за дефинисање филтера за венчања у бази података.
"""

import django_filters
from django.db import models
from django.db.models.functions import Cast

from registar.models import Vencanje


class VencanjeFilter(django_filters.FilterSet):
    """Филтер за претрагу венчања на основу различитих поља."""

    search = django_filters.CharFilter(method="filter_search", label="Претрага")

    class Meta:
        model = Vencanje
        fields = []

    def filter_search(self, queryset, name, value):
        """Претражује уносе на основу више текстуалних поља, укључујући датум."""
        termini_pretrage = value.split()
        queryset = queryset.annotate(
            datum_str=Cast("datum", models.CharField())
        )

        query = models.Q()
        for rec in termini_pretrage:
            query &= (
                models.Q(ime_zenika__icontains=rec)
                | models.Q(prezime_zenika__icontains=rec)
                | models.Q(ime_neveste__icontains=rec)
                | models.Q(prezime_neveste__icontains=rec)
                | models.Q(kum__icontains=rec)
                | models.Q(stari_svat__icontains=rec)
                | models.Q(hram__naziv__icontains=rec)
                | models.Q(datum_str__icontains=rec)
            )
        return queryset.filter(query)
