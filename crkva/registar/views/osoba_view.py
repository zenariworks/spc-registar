from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from weasyprint import HTML

from registar.models.osoba import Osoba
from registar.forms import SearchForm


class OsobeList(ListView):
    template_name = "registar/spisak_osoba.html"
    context_object_name = "osobe_entries"
    model = Osoba  # or queryset = Krstenje.objects.all()

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            return Osoba.objects.filter(dete__ime__icontains=query)
        return Osoba.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(self.request.GET)
        return context


class OsobaPDF(DetailView):
    model = Osoba
    template_name = "registar/pdf_osoba.html"

    def get_object(self):
        uid = self.kwargs.get("uid")
        return get_object_or_404(Osoba, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        # Render the HTML template with context
        html_string = render(self.request, self.template_name, context).content.decode()

        # Convert the HTML to PDF using WeasyPrint
        pdf = HTML(string=html_string, base_url=self.request.build_absolute_uri()).write_pdf()

        # Create and return an HTTP response with the PDF
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f"inline; filename=krstenje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

class OsobaView(DetailView):
    model = Osoba
    template_name = "registar/info_osoba.html"
    context_object_name = "osoba"
    pk_url_kwarg = "uid"

    font_name = "DejaVuSans"

    def get_object(self):
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Osoba, uid=uid)
