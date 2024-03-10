from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from registar.forms import SearchForm
from registar.models.svestenik import Svestenik
from weasyprint import HTML


class SvesteniciSpisak(ListView):
    model = Svestenik
    template_name = "registar/spisak_svestenika.html"
    context_object_name = "svestenici"

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            return Svestenik.objects.filter(dete__ime__icontains=query)
        return Svestenik.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(self.request.GET)
        return context


class SvestenikPDF(DetailView):
    model = Svestenik
    template_name = "registar/pdf_svestenik.html"

    def get_object(self):
        uid = self.kwargs.get("uid")
        return get_object_or_404(Svestenik, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        # Render the HTML template with context
        html = render(self.request, self.template_name, context).content.decode()

        # Convert the HTML to PDF using WeasyPrint
        pdf = HTML(string=html, base_url=self.request.build_absolute_uri()).write_pdf()

        # Create and return an HTTP response with the PDF
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=krstenje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class SvestenikPrikaz(DetailView):
    model = Svestenik
    template_name = "registar/info_svestenik.html"
    context_object_name = "svestenik"

    font_name = "DejaVuSans"

    def get_object(self):
        uid = self.kwargs.get("uid")
        return get_object_or_404(Svestenik, uid=uid)
