import django_filters
from registar.models.krstenje import Krstenje


class KrstenjeFilter(django_filters.FilterSet):
    datum = django_filters.DateFilter(
        field_name="datum", lookup_expr="exact", label="Датум"
    )
    ime_deteta = django_filters.CharFilter(
        field_name="ime_deteta", lookup_expr="icontains", label="Име детета"
    )
    ime_oca = django_filters.CharFilter(
        field_name="ime_oca", lookup_expr="icontains", label="Име оца"
    )
    ime_majke = django_filters.CharFilter(
        field_name="ime_majke", lookup_expr="icontains", label="Име мајке"
    )
    hram = django_filters.CharFilter(
        field_name="hram__naziv", lookup_expr="icontains", label="Храм"
    )

    class Meta:
        model = Krstenje
        fields = ["datum", "ime_deteta", "ime_oca", "ime_majke", "hram"]
