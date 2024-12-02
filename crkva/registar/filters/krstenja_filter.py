"""
Модул за дефинисање филтера за крштења у бази података.
"""

import django_filters
from django.db import models
from django.db.models.functions import Cast

from registar.models import Krstenje


class KrstenjeFilter(django_filters.FilterSet):
    """Филтер за претрагу крштења на основу различитих поља."""

    search = django_filters.CharFilter(method="filter_search", label="")

    class Meta:
        model = Krstenje
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
                models.Q(ime_deteta__icontains=rec)
                | models.Q(gradjansko_ime_deteta__icontains=rec)
                | models.Q(ime_oca__icontains=rec)
                | models.Q(prezime_oca__icontains=rec)
                | models.Q(ime_majke__icontains=rec)
                | models.Q(prezime_majke__icontains=rec)
                | models.Q(ime_kuma__icontains=rec)
                | models.Q(prezime_kuma__icontains=rec)
                | models.Q(datum_str__icontains=rec)
            )
        return queryset.filter(query)
