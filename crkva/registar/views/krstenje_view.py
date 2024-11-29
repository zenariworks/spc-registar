"""
Модул за приказ, унос и генерисање PDF докумената за крштења.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView
from django_filters.views import FilterView
from registar.filters import KrstenjeFilter
from registar.forms import KrstenjeForm
from registar.models import Krstenje
from weasyprint import HTML


def unos_krstenja(request):
    """
    Обрађује захтеве за унос новог крштења. Ако је захтев POST,
    чува податке у базу, иначе приказује формулар за унос.
    """
    if request.method == "POST":
        form = KrstenjeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("krstenja")
    else:
        form = KrstenjeForm()
    return render(request, "registar/unos_krstenja.html", {"form": form})


class SpisakKrstenja(FilterView, ListView):
    """Приказује списак крштења са могућностима претраге и пагинације."""

    model = Krstenje
    template_name = "registar/spisak_krstenja.html"
    context_object_name = "krstenja"
    paginate_by = 10
    filterset_class = KrstenjeFilter

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


class KrstenjePDF(DetailView):
    """Генерише PDF документ за одређено крштење."""

    model = Krstenje
    template_name = "registar/pdf_krstenje.html"
    context_object_name = "krstenje"

    def get_object(self, queryset=None):
        """Враћа објекат крштења на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Krstenje, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        """Претвара HTML садржај у PDF и враћа HTTP одговор са PDF документом."""
        html = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(string=html, base_url=self.request.build_absolute_uri()).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=krstenje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтеве за генерисање PDF-а."""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazKrstenja(DetailView):
    """Приказује детаљне информације о појединачном крштењу."""

    model = Krstenje
    template_name = "registar/info_krstenje.html"
    context_object_name = "krstenje"

    def get_object(self) -> Krstenje:
        """Враћа објекат крштења на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Krstenje, uid=uid)
