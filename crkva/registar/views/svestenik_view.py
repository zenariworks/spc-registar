from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from easy_pdf.views import PDFTemplateResponseMixin

from registar.models.svestenik import Svestenik


class SvestenikPDF(PDFTemplateResponseMixin, DetailView):
    model = Svestenik
    template_name = "registar/print_svestenik.html"


class SvestenikView(DetailView):
    model = Svestenik
    template_name = "registar/view_svestenik.html"
    context_object_name = "svestenik"
    pk_url = "uid"

    font_name = "DejaVuSans"

    def get_object(self):
        uid = self.kwargs.get(self.pk_url)
        return get_object_or_404(Svestenik, uid=uid)
