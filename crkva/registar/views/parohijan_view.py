"""
Модул за приказ, додавање и генерисање PDF докумената за парохијане.
"""

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView
from registar.forms import ParohijanForm, SearchForm
from registar.utils import get_query_variants
from registar.models.parohijan import Parohijan
from weasyprint import HTML


def unos_parohijana(request):
    """
    Обрађује захтев за додавање новог парохијана. Ако је метод POST,
    подаци се чувају у базу. У супротном, приказује се формулар за унос.
    """
    if request.method == "POST":
        form = ParohijanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("parohijani")
    else:
        form = ParohijanForm()
    return render(request, "registar/unos_parohijana.html", {"form": form})


class SpisakParohijana(ListView):
    """Приказује списак парохијана са могућношћу претраге и пагинације."""
    model = Parohijan
    template_name = "registar/spisak_parohijana.html"
    context_object_name = "parohijani"
    paginate_by = 10

    def get_queryset(self):
        """Филтрира парохијане на основу унетог појма у форми за претрагу."""
        form = SearchForm(data=self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get("search", "")
            if not query:
                return Parohijan.objects.all()
            variants = get_query_variants(query)
            q = None
            for v in variants:
                clause = Q(ime__icontains=v) | Q(prezime__icontains=v)
                q = clause if q is None else (q | clause)
            return Parohijan.objects.filter(q) if q is not None else Parohijan.objects.all()
        return Parohijan.objects.all()

    def get_context_data(self, **kwargs):
        """Додаје форму за претрагу у контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(data=self.request.GET)
        context["upit"] = self.request.GET.get("search", "")
        return context


class ParohijanPDF(DetailView):
    """Генерише PDF документ за одређеног парохијана."""
    model = Parohijan
    template_name = "registar/pdf_parohijan.html"

    def get_object(self, queryset=None):
        """Преузима парохијана на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Parohijan, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        """Претвара HTML садржај у PDF и враћа HTTP одговор са PDF документом."""
        html_string = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(
            string=html_string, base_url=self.request.build_absolute_uri()
        ).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(content=pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=parohijan-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтев за генерисање PDF документа за парохијана."""
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazParohijana(DetailView):
    """Приказује детаљне информације о одређеном парохијану."""
    model = Parohijan
    template_name = "registar/info_parohijan.html"
    context_object_name = "parohijan"
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        """Преузима парохијана на основу UID-а."""
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Parohijan, uid=uid)
