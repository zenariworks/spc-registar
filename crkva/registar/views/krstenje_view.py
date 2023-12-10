from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from easy_pdf.views import PDFTemplateResponseMixin

from registar.models.krstenje import Krstenje
from registar.forms import SearchForm


class KrstenjaList(ListView):
    model = Krstenje
    template_name = "registar/krstenja_list.html"
    context_object_name = "krstenja"

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            return Krstenje.objects.filter(dete__name__icontains=query)
        return Krstenje.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(self.request.GET)
        return context


class KrstenjePDF(PDFTemplateResponseMixin, DetailView):
    model = Krstenje
    template_name = "registar/krstenje_print.html"

    def get_object(self, queryset=None):
        uid = self.kwargs.get("uid")
        return get_object_or_404(Krstenje, uid=uid)


class KrstenjeView(DetailView):
    model = Krstenje
    template_name = "registar/krstenje_view.html"
    context_object_name = "krstenje"
    pk_url = "uid"

    font_name = "DejaVuSans"

    def get_object(self):
        k_rbr = self.kwargs.get(self.pk_url)
        return get_object_or_404(Krstenje, uid=k_rbr)
