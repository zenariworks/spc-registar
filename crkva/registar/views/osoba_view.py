from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from easy_pdf.views import PDFTemplateResponseMixin

from registar.models.osoba import Osoba
from registar.forms import SearchForm


class OsobeListView(ListView):
    template_name = 'registar/osobe.html'
    context_object_name = 'osobe_entries'
    model = Osoba  # or queryset = Krstenje.objects.all()

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            return Osoba.objects.filter(dete__ime__icontains=query)
        return Osoba.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SearchForm(self.request.GET)
        return context
    

class OsobaPDF(PDFTemplateResponseMixin, DetailView):
    model = Osoba
    template_name = "registar/osoba_print.html"
    pk_url_kwarg = "uid"

    def get_object(self):
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Osoba, uid=uid)


class OsobaView(DetailView):
    model = Osoba
    template_name = "registar/osoba_view.html"
    context_object_name = "osoba"
    pk_url_kwarg = "uid"

    font_name = "DejaVuSans"

    def get_object(self):
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Osoba, uid=uid)