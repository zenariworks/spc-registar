"""
Модул за приказ, претрагу и генерисање PDF докумената за свештенике.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from registar.forms import SvestenikForm
from registar.models.svestenik import Svestenik
from registar.views.base import EditChromeMixin, RegistarCreateView, RegistarUpdateView
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from registar.views.pdf import HistorySnapshotMixin, PdfDetailView


class SvestenikCreate(RegistarCreateView):
    """Унос новог свештеника."""

    form_class = SvestenikForm
    template_name = "registar/svestenik.html"
    context_object_name = "svestenik"
    role = "svestenik"
    success_url_name = "svestenici"


unos_svestenika = SvestenikCreate.as_view()


class SpisakSvestenika(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак свештеника са могућностима претраге и пагинације."""

    model = Svestenik
    template_name = "registar/spisak_svestenika.html"
    partial_template_name = "_partials/_stavka_svestenika.html"
    context_object_name = "svestenici"
    paginate_by = 10
    search_fields = ["ime", "prezime", "zvanje"]
    sort_options = [
        ("prezime", "Презиме А-Ш"),
        ("-prezime", "Презиме Ш-А"),
        ("zvanje", "Звање"),
    ]
    ordering = ["prezime", "ime"]

    def get_queryset(self):
        return self.get_search_queryset(
            Svestenik.objects.select_related("parohija").all()
        )


class SvestenikPDF(HistorySnapshotMixin, PdfDetailView):
    """Генерише PDF документ за одређеног свештеника."""

    model = Svestenik
    template_name = "registar/pdf_svestenik.html"
    filename_prefix = "svestenik"


class PrikazSvestenika(LoginRequiredMixin, DetailView):
    """Приказује детаљне информације о одређеном свештенику."""

    model = Svestenik
    template_name = "registar/svestenik.html"
    context_object_name = "svestenik"

    def get_object(self):
        """Враћа објекат свештеника на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Svestenik.objects.select_related("parohija"), uid=uid)

    def get_context_data(self, **kwargs):
        from registar.istorija import history_for

        context = super().get_context_data(**kwargs)
        context["history_entries"] = history_for(self.object)
        context["form"] = SvestenikForm(instance=self.object)
        context["is_edit"] = False
        s = self.object
        context["krstenja"] = s.свештеник_крститељ.select_related(
            "dete", "otac"
        ).order_by("-datum")[:20]
        context["krstenja_count"] = s.свештеник_крститељ.count()
        context["vencanja"] = s.свештеник_венчани.select_related(
            "zenik", "nevesta"
        ).order_by("-datum")[:20]
        context["vencanja_count"] = s.свештеник_венчани.count()
        return context


class SvestenikUpdate(EditChromeMixin, RegistarUpdateView):
    """Измена постојећег свештеника."""

    model = Svestenik
    form_class = SvestenikForm
    template_name = "registar/svestenik.html"
    context_object_name = "svestenik"
    role = "svestenik"
    detail_url_name = "svestenik_detail"


izmena_svestenika = SvestenikUpdate.as_view()
