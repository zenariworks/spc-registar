from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from django_filters.views import FilterView
from registar.filters import VencanjeFilter
from registar.models.vencanje import Vencanje
from weasyprint import HTML


class SpisakVencanja(FilterView, ListView):
    model = Vencanje
    template_name = "registar/spisak_vencanja.html"
    context_object_name = "vencanja"
    paginate_by = 10
    filterset_class = VencanjeFilter

    def get_queryset(self):
        return self.filterset_class(
            self.request.GET, queryset=super().get_queryset()
        ).qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset_class(
            self.request.GET, queryset=self.get_queryset()
        )
        return context


class VencanjePDF(DetailView):
    model = Vencanje
    template_name = "registar/pdf_vencanje.html"
    context_object_name = "vencanje"

    def get_object(self, queryset=None):
        uid = self.kwargs.get("uid")
        return get_object_or_404(Vencanje, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        # Render the HTML template with context
        html_string = render(self.request, self.template_name, context).content.decode()

        # Convert the HTML to PDF using WeasyPrint
        pdf = HTML(
            string=html_string, base_url=self.request.build_absolute_uri()
        ).write_pdf()

        # Create and return an HTTP response with the PDF
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=vencanje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazVencanja(DetailView):
    model = Vencanje
    template_name = "registar/info_vencanje.html"
    context_object_name = "vencanje"

    font_name = "DejaVuSans"

    def get_object(self) -> Vencanje:
        uid = self.kwargs.get("uid")
        return get_object_or_404(Vencanje, uid=uid)
