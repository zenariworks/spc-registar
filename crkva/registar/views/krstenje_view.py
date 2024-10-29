from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView
from django_filters.views import FilterView
from registar.filters import KrstenjeFilter
from registar.forms import KrstenjeForm
from registar.models import Krstenje
from weasyprint import HTML


def unos_krstenja(request):
    if request.method == "POST":
        form = KrstenjeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("krstenja")
    else:
        form = KrstenjeForm()
    return render(request, "registar/unos_krstenja.html", {"form": form})


class SpisakKrstenja(FilterView, ListView):
    model = Krstenje
    template_name = "registar/spisak_krstenja.html"
    context_object_name = "krstenja"
    paginate_by = 10
    filterset_class = KrstenjeFilter

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


class KrstenjePDF(DetailView):
    model = Krstenje
    template_name = "registar/pdf_krstenje.html"
    # template_name = "registar/pdf_krstenje_stara_krstenica.html"
    context_object_name = "krstenje"

    def get_object(self, queryset=None):
        uid = self.kwargs.get("uid")
        return get_object_or_404(Krstenje, uid=uid)

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
        response["Content-Disposition"] = f"inline; filename=krstenje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazKrstenja(DetailView):
    model = Krstenje
    template_name = "registar/info_krstenje.html"
    context_object_name = "krstenje"

    font_name = "DejaVuSans"

    def get_object(self) -> Krstenje:
        uid = self.kwargs.get("uid")
        return get_object_or_404(Krstenje, uid=uid)
