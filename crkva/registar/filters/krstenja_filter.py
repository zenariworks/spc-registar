"""
Модул за дефинисање филтера за крштења у бази података.
"""

import django_filters
from django.db import models
from registar.models import Krstenje


class KrstenjeFilter(django_filters.FilterSet):
    """Филтер за претрагу крштења на основу различитих поља."""

    search = django_filters.CharFilter(method="filter_search", label="")

    class Meta:
        model = Krstenje
        fields = []

    def filter_search(self, queryset, name, value):
        """Претражује уносе на основу више текстуалних поља."""
        return queryset.filter(
            models.Q(ime_deteta__icontains=value)
            | models.Q(gradjansko_ime_deteta__icontains=value)
            | models.Q(ime_oca__icontains=value)
            | models.Q(prezime_oca__icontains=value)
            | models.Q(ime_majke__icontains=value)
            | models.Q(prezime_majke__icontains=value)
            | models.Q(ime_kuma__icontains=value)
            | models.Q(prezime_kuma__icontains=value)
        )
