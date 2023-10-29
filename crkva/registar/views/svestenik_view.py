from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from easy_pdf.views import PDFTemplateResponseMixin

from registar.models.svestenik import Svestenik


class SvesteniciList(ListView):
    template_name = 'registar/svestenici.html'
    context_object_name = 'svestenici_entries'
    model = Svestenik  # or queryset = Krstenje.objects.all()

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            return Svestenik.objects.filter(dete__ime__icontains=query)
        return Svestenik.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = SearchForm(self.request.GET)
        return context


class SvestenikPDF(PDFTemplateResponseMixin, DetailView):
    model = Svestenik
    template_name = "registar/svestenik_print.html"


class SvestenikView(DetailView):
    model = Svestenik
    template_name = "registar/svestenik_view.html"
    context_object_name = "svestenik"
    pk_url = "uid"

    font_name = "DejaVuSans"

    def get_object(self):
        uid = self.kwargs.get(self.pk_url)
        return get_object_or_404(Svestenik, uid=uid)
