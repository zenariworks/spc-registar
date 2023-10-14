from django.shortcuts import render
from django.views.generic import DetailView

from easy_pdf.views import PDFTemplateResponseMixin

from .models import Svestenik


class SvestenikPDFView(PDFTemplateResponseMixin, DetailView):
    model = Svestenik
    template_name = 'registar/print_svestenik.html'


def svestenik_detail(request, sv_rbr):
    svestenik = Svestenik.objects.get(sv_rbr=sv_rbr)
    return render(request, 'registar/view_svestenik.html', {'svestenik': svestenik})


def index(request):
    return render(request, 'registar/index.html')
