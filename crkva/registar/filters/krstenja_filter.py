"""
Модул за дефинисање филтера за крштења у бази података.
"""

import django_filters
from django.db import models
from django.db.models.functions import Cast
from registar.models import Krstenje
from registar.utils import get_query_variants


class KrstenjeFilter(django_filters.FilterSet):
    """Филтер за претрагу крштења на основу различитих поља."""

    search = django_filters.CharFilter(method="filter_search", label="")

    class Meta:
        model = Krstenje
        fields = []

    def filter_search(self, queryset, _name, value):
        """Претражује уносе на основу више текстуалних поља, укључујући датум."""
        termini_pretrage = value.split()
        queryset = queryset.annotate(datum_str=Cast("datum", models.CharField()))

        query = models.Q()
        for rec in termini_pretrage:
            # За сваки термин направи OR клаузулу преко свих варијанти (латиница/ћирилица)
            inner = models.Q()
            for v in get_query_variants(rec):
                inner |= (
                    models.Q(ime_deteta__icontains=v)
                    | models.Q(gradjansko_ime_deteta__icontains=v)
                    | models.Q(ime_oca__icontains=v)
                    | models.Q(prezime_oca__icontains=v)
                    | models.Q(ime_majke__icontains=v)
                    | models.Q(prezime_majke__icontains=v)
                    | models.Q(ime_kuma__icontains=v)
                    | models.Q(prezime_kuma__icontains=v)
                    | models.Q(datum_str__icontains=v)
                )
            # Сви термини морају да се пронађу (AND)
            query &= inner
        return queryset.filter(query)
