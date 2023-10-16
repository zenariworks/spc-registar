from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from easy_pdf.views import PDFTemplateResponseMixin

from registar.models.krstenje import Krstenje


class KrstenjePDF(PDFTemplateResponseMixin, DetailView):
    model = Krstenje
    template_name = 'registar/print_krstenje.html'


class KrstenjeView(DetailView):
    model = Krstenje
    template_name = 'registar/view_krstenje.html'
    context_object_name = 'krstenje'
    pk_url_kwarg = 'k_rbr'

    font_name = 'DejaVuSans'

    def get_object(self):
        k_rbr = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Krstenje, k_rbr=k_rbr)