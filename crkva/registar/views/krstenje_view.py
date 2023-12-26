from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView

from weasyprint import HTML

from registar.models.krstenje import Krstenje
from registar.forms import SearchForm


class KrstenjeSpisak(ListView):
    model = Krstenje
    template_name = "registar/spisak_krstenja.html"
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


class KrstenjePDF(DetailView):
    model = Krstenje
    template_name = "registar/pdf_krstenje.html"
    context_object_name = "krstenje"

    def get_object(self, queryset=None):
        uid = self.kwargs.get("uid")
        return get_object_or_404(Krstenje, uid=uid)

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



class KrstenjePrikaz(DetailView):
    model = Krstenje
    template_name = "registar/info_krstenje.html"
    context_object_name = "krstenje"

    font_name = "DejaVuSans"

    def get_object(self):
        k_rbr = self.kwargs.get("uid")
        return get_object_or_404(Krstenje, uid=k_rbr)
