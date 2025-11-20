"""
Модул за дефинисање филтера за венчања у бази података.
"""

import django_filters
from django.db import models
from django.db.models.functions import Cast

from registar.models import Vencanje
from registar.utils import get_query_variants


class VencanjeFilter(django_filters.FilterSet):
    """Филтер за претрагу венчања на основу различитих поља."""

    search = django_filters.CharFilter(method="filter_search", label="Претрага")

    class Meta:
        model = Vencanje
        fields = []

    def filter_search(self, queryset, _name, value):
        """Претражује уносе на основу више текстуалних поља, укључујући датум."""
        termini_pretrage = value.split()
        queryset = queryset.annotate(
            datum_str=Cast("datum", models.CharField())
        )

        query = models.Q()
        for rec in termini_pretrage:
            inner = models.Q()
            for v in get_query_variants(rec):
                inner |= (
                    models.Q(ime_zenika__icontains=v)
                    | models.Q(prezime_zenika__icontains=v)
                    | models.Q(ime_neveste__icontains=v)
                    | models.Q(prezime_neveste__icontains=v)
                    | models.Q(kum__icontains=v)
                    | models.Q(stari_svat__icontains=v)
                    | models.Q(hram__naziv__icontains=v)
                    | models.Q(datum_str__icontains=v)
                )
            query &= inner
        return queryset.filter(query)
