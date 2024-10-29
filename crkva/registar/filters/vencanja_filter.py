import django_filters
from registar.models import Vencanje


class VencanjeFilter(django_filters.FilterSet):
    datum = django_filters.DateFilter(
        field_name="datum", lookup_expr="exact", label="Датум"
    )
    ime_zenika = django_filters.CharFilter(
        field_name="ime_zenika", lookup_expr="icontains", label="Име женика"
    )
    prezime_zenika = django_filters.CharFilter(
        field_name="prezime_zenika", lookup_expr="icontains", label="Презиме женика"
    )
    ime_neveste = django_filters.CharFilter(
        field_name="ime_neveste", lookup_expr="icontains", label="Име невесте"
    )
    prezime_neveste = django_filters.CharFilter(
        field_name="prezime_neveste", lookup_expr="icontains", label="Презиме невесте"
    )
    hram = django_filters.CharFilter(
        field_name="hram__naziv", lookup_expr="icontains", label="Храм"
    )

    class Meta:
        model = Vencanje
        fields = [
            "datum",
            "ime_zenika",
            "prezime_zenika",
            "ime_neveste",
            "prezime_neveste",
            "hram",
        ]
