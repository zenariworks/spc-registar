from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView
from registar.forms import ParohijanForm, SearchForm
from registar.models.parohijan import Parohijan
from weasyprint import HTML


def unos_parohijana(request):
    """Додавање новог парохијана."""
    if request.method == "POST":
        form = ParohijanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("parohijani")
    else:
        form = ParohijanForm()
    return render(request, "registar/unos_parohijana.html", {"form": form})


class SpisakParohijana(ListView):
    model = Parohijan
    template_name = "registar/spisak_parohijana.html"
    context_object_name = "parohijani"
    paginate_by = 10

    def get_queryset(self):
        """Приказ списка парохијана са могућношћу претраге."""
        form = SearchForm(data=self.request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            return Parohijan.objects.filter(dete__ime__icontains=query)
        return Parohijan.objects.all()

    def get_context_data(self, **kwargs):
        """Додавање форме за претрагу у контекст."""
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(data=self.request.GET)
        return context


class ParohijanPDF(DetailView):
    model = Parohijan
    template_name = "registar/pdf_parohijan.html"

    def get_object(self, queryset=None):
        """Преузимање парохијана на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Parohijan, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        """Генерисање и приказ ПДФ-а парохијана."""
        html_string = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(
            string=html_string, base_url=self.request.build_absolute_uri()
        ).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(content=pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=krstenje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Приказ странице за парохијана у ПДФ формату."""
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazParohijana(DetailView):
    model = Parohijan
    template_name = "registar/info_parohijan.html"
    context_object_name = "parohijan"
    pk_url_kwarg = "uid"

    font_name = "DejaVuSans"

    def get_object(self, queryset=None):
        """Преузимање парохијана на основу UID-а."""
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Parohijan, uid=uid)
