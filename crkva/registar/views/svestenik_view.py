"""
Модул за приказ, претрагу и генерисање PDF докумената за свештенике.
"""

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from registar.forms import SearchForm
from registar.models.svestenik import Svestenik
from registar.utils import get_query_variants
from weasyprint import HTML


class SpisakSvestenika(ListView):
    """Приказује списак свештеника са могућностима претраге и пагинације."""

    model = Svestenik
    template_name = "registar/spisak_svestenika.html"
    context_object_name = "svestenici"
    paginate_by = 10

    def get_queryset(self):
        """Филтрира податке на основу унетог појма у форми за претрагу."""
        form = SearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get("search", "")
            if not query:
                return Svestenik.objects.all()
            q = None
            for v in get_query_variants(query):
                clause = (
                    Q(ime__icontains=v)
                    | Q(prezime__icontains=v)
                    | Q(zvanje__icontains=v)
                )
                q = clause if q is None else (q | clause)
            return (
                Svestenik.objects.filter(q)
                if q is not None
                else Svestenik.objects.all()
            )
        return Svestenik.objects.all()

    def get_context_data(self, **kwargs):
        """Додаје формулар за претрагу у контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(self.request.GET)
        context["upit"] = self.request.GET.get("search", "")
        return context


class SvestenikPDF(DetailView):
    """Генерише PDF документ за одређеног свештеника."""

    model = Svestenik
    template_name = "registar/pdf_svestenik.html"

    def get_object(self):
        """Враћа објекат свештеника на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Svestenik, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        """Претвара HTML садржај у PDF и враћа HTTP одговор са PDF документом."""
        html = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(string=html, base_url=self.request.build_absolute_uri()).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=svestenik-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтеве за генерисање PDF-а."""
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazSvestenika(DetailView):
    """Приказује детаљне информације о одређеном свештенику."""

    model = Svestenik
    template_name = "registar/info_svestenik.html"
    context_object_name = "svestenik"

    def get_object(self):
        """Враћа објекат свештеника на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Svestenik, uid=uid)
