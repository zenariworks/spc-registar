"""
Модул за приказ, претрагу и генерисање PDF докумената за венчања."""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from django_filters.views import FilterView
from registar.filters import VencanjeFilter
from registar.models.vencanje import Vencanje
from weasyprint import HTML


class SpisakVencanja(FilterView, ListView):
    """Приказује списак венчања са могућностима претраге и пагинације."""

    model = Vencanje
    template_name = "registar/spisak_vencanja.html"
    context_object_name = "vencanja"
    paginate_by = 10
    filterset_class = VencanjeFilter

    def get_queryset(self):
        """Филтрира податке на основу захтева корисника."""
        return self.filterset_class(
            self.request.GET, queryset=super().get_queryset()
        ).qs

    def get_context_data(self, **kwargs):
        """Додаје филтер и претражени текст у контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset_class(
            self.request.GET, queryset=self.get_queryset()
        )
        context["search_query"] = self.request.GET.get("search", "")
        return context


class VencanjePDF(DetailView):
    """Генерише PDF документ за одређено венчање."""

    model = Vencanje
    template_name = "registar/pdf_vencanje.html"
    context_object_name = "vencanje"

    def get_object(self, queryset=None):
        """Враћа објекат венчања на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Vencanje, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        """Претвара HTML садржај у PDF и враћа HTTP одговор са PDF документом."""
        html = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(string=html, base_url=self.request.build_absolute_uri()).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=vencanje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтеве за генерисање PDF-а."""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazVencanja(DetailView):
    """Приказује детаљне информације о појединачном венчању."""

    model = Vencanje
    template_name = "registar/info_vencanje.html"
    context_object_name = "vencanje"

    def get_object(self) -> Vencanje:
        """Враћа објекат венчања на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Vencanje, uid=uid)
