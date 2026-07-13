"""
Модул за приказ, унос и генерисање PDF докумената за крштења.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from registar.forms import KrstenjeForm
from registar.models import Krstenje
from registar.services.izdavalac import get_izdavalac
from registar.views.base import RegistarCreateView, RegistarUpdateView
from registar.views.calibrate import render_calibrate
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from registar.views.pdf import HistorySnapshotMixin, PdfDetailView
from tenants.permissions import tenant_role_required

KRSTENJE_RELATED = (
    "dete",
    "otac",
    "majka",
    "kum",
    "hram",
    "svestenik",
)


class KrstenjeCreate(RegistarCreateView):
    """Унос новог крштења."""

    form_class = KrstenjeForm
    template_name = "registar/krstenje.html"
    context_object_name = "krstenje"
    role = "krstenje"
    success_url_name = "krstenja"


unos_krstenja = KrstenjeCreate.as_view()


class SpisakKrstenja(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак крштења са могућностима претраге и пагинације."""

    model = Krstenje
    template_name = "registar/spisak_krstenja.html"
    partial_template_name = "_partials/_stavka_krstenja.html"
    context_object_name = "krstenja"
    paginate_by = 10
    search_fields = [
        "dete__ime",
        "dete__gradjansko_ime",
        "otac__ime",
        "otac__prezime",
        "majka__ime",
        "majka__prezime",
        "kum__ime",
        "kum__prezime",
    ]
    search_date_field = "datum"
    sort_options = [
        ("datum", "Датум растуће"),
        ("-datum", "Датум опадајуће"),
    ]

    def get_queryset(self):
        return self.get_search_queryset(
            Krstenje.objects.select_related(*KRSTENJE_RELATED).order_by("datum")
        )


class KrstenjePDF(HistorySnapshotMixin, PdfDetailView):
    """Генерише PDF документ за одређено крштење."""

    model = Krstenje
    template_name = "registar/pdf_krstenje.html"
    context_object_name = "krstenje"
    related = KRSTENJE_RELATED
    filename_prefix = "krstenje"
    snapshot_roles = ["dete", "otac", "majka", "kum"]


class PrikazKrstenja(LoginRequiredMixin, DetailView):
    """Приказује детаљне информације о појединачном крштењу."""

    model = Krstenje
    template_name = "registar/krstenje.html"
    context_object_name = "krstenje"

    def get_object(self) -> Krstenje:
        """Враћа објекат крштења на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(
            Krstenje.objects.select_related(*KRSTENJE_RELATED),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Form bound to instance + is_edit=False so the unified template renders."""
        context = super().get_context_data(**kwargs)
        context["form"] = KrstenjeForm(instance=self.object)
        context["is_edit"] = False
        context["izdavalac"] = get_izdavalac(self.request)
        return context


@tenant_role_required("krstenje")
def calibrate_krstenje(request):
    """Калибрациона страница за подешавање позиција поља на крштеници."""
    return render_calibrate(request, "krstenje")


class KrstenjeUpdate(RegistarUpdateView):
    """Измена постојећег крштења."""

    model = Krstenje
    form_class = KrstenjeForm
    template_name = "registar/krstenje.html"
    context_object_name = "krstenje"
    role = "krstenje"
    detail_url_name = "krstenje_detail"


izmena_krstenja = KrstenjeUpdate.as_view()
