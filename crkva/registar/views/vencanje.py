"""
Модул за приказ, унос, претрагу и генерисање PDF докумената за венчања.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from registar.forms import VencanjeForm
from registar.models.vencanje import Vencanje
from registar.services.izdavalac import get_izdavalac
from registar.views.base import RegistarCreateView, RegistarUpdateView
from registar.views.calibrate import render_calibrate
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from registar.views.pdf import HistorySnapshotMixin, PdfDetailView
from tenants.permissions import tenant_role_required

VENCANJE_RELATED = (
    "zenik",
    "nevesta",
    "kum",
    "svekar",
    "svekrva",
    "tast",
    "tasta",
    "stari_svat",
    "hram",
    "svestenik",
)


class SpisakVencanja(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак венчања са могућностима претраге и пагинације."""

    model = Vencanje
    template_name = "registar/spisak_vencanja.html"
    partial_template_name = "_partials/_stavka_vencanja.html"
    context_object_name = "vencanja"
    paginate_by = 10
    search_fields = [
        "zenik__ime",
        "zenik__prezime",
        "nevesta__ime",
        "nevesta__prezime",
        "kum__ime",
        "stari_svat__ime",
        "hram__naziv",
    ]
    search_date_field = "datum"
    sort_options = [
        ("datum", "Датум растуће"),
        ("-datum", "Датум опадајуће"),
    ]

    def get_queryset(self):
        return self.get_search_queryset(
            Vencanje.objects.select_related(*VENCANJE_RELATED).order_by("datum")
        )


class VencanjePDF(HistorySnapshotMixin, PdfDetailView):
    """Генерише PDF документ за одређено венчање."""

    model = Vencanje
    template_name = "registar/pdf_vencanje.html"
    context_object_name = "vencanje"
    related = VENCANJE_RELATED
    filename_prefix = "vencanje"
    snapshot_roles = [
        "zenik",
        "nevesta",
        "kum",
        "svekar",
        "svekrva",
        "tast",
        "tasta",
        "stari_svat",
    ]


class PrikazVencanja(LoginRequiredMixin, DetailView):
    """Приказује детаљне информације о појединачном венчању."""

    model = Vencanje
    template_name = "registar/vencanje.html"
    context_object_name = "vencanje"

    def get_object(self) -> Vencanje:
        """Враћа објекат венчања на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(
            Vencanje.objects.select_related(*VENCANJE_RELATED),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Form bound to instance + is_edit=False so the unified template renders."""
        context = super().get_context_data(**kwargs)
        context["form"] = VencanjeForm(instance=self.object)
        context["is_edit"] = False
        context["izdavalac"] = get_izdavalac(self.request)
        return context


class VencanjeCreate(RegistarCreateView):
    """Унос новог венчања."""

    form_class = VencanjeForm
    template_name = "registar/vencanje.html"
    context_object_name = "vencanje"
    role = "vencanje"
    success_url_name = "vencanja"


unos_vencanja = VencanjeCreate.as_view()


@tenant_role_required("vencanje")
def calibrate_vencanje(request):
    """Приказује страницу за калибрацију позиција поља на венчаници."""
    return render_calibrate(request, "vencanje")


class VencanjeUpdate(RegistarUpdateView):
    """Измена постојећег венчања."""

    model = Vencanje
    form_class = VencanjeForm
    template_name = "registar/vencanje.html"
    context_object_name = "vencanje"
    role = "vencanje"
    detail_url_name = "vencanje_detail"


izmena_vencanja = VencanjeUpdate.as_view()
