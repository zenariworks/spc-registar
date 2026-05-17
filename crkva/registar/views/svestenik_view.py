"""
Модул за приказ, претрагу и генерисање PDF докумената за свештенике.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from registar.forms import SvestenikForm
from registar.models.svestenik import Svestenik
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from tenants.permissions import tenant_role_required
from weasyprint import HTML


@tenant_role_required("svestenik")
def unos_svestenika(request):
    """Обрађује захтев за додавање новог свештеника."""
    if request.method == "POST":
        form = SvestenikForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("svestenici")
    else:
        form = SvestenikForm()
    return render(
        request,
        "registar/svestenik.html",
        {"form": form, "is_edit": True, "svestenik": None},
    )


class SpisakSvestenika(SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView):
    """Приказује списак свештеника са могућностима претраге и пагинације."""

    model = Svestenik
    template_name = "registar/spisak_svestenika.html"
    partial_template_name = "registar/_stavka_svestenika.html"
    context_object_name = "svestenici"
    paginate_by = 10
    search_fields = ["ime", "prezime", "zvanje"]
    sort_options = [
        ("prezime", "Презиме А-Ш"),
        ("-prezime", "Презиме Ш-А"),
        ("zvanje", "Звање"),
    ]
    ordering = ["prezime", "ime"]

    def get_queryset(self):
        return self.get_search_queryset(
            Svestenik.objects.select_related("parohija").all()
        )


class SvestenikPDF(DetailView):
    """Генерише PDF документ за одређеног свештеника."""

    model = Svestenik
    template_name = "registar/pdf_svestenik.html"

    def get_object(self):
        """Враћа објекат свештеника на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Svestenik, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        """Претвара HTML садржај у PDF и враћа HTTP одговор са PDF документом."""
        html = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(string=html, base_url=self.request.build_absolute_uri()).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=svestenik-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтеве за генерисање PDF-а."""
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazSvestenika(DetailView):
    """Приказује детаљне информације о одређеном свештенику."""

    model = Svestenik
    template_name = "registar/svestenik.html"
    context_object_name = "svestenik"

    def get_object(self):
        """Враћа објекат свештеника на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Svestenik.objects.select_related("parohija"), uid=uid)

    def get_context_data(self, **kwargs):
        from registar.history import history_for

        context = super().get_context_data(**kwargs)
        context["history_entries"] = history_for(self.object)
        s = self.object
        context["krstenja"] = s.свештеник_крститељ.select_related(
            "dete", "otac"
        ).order_by("-datum")[:20]
        context["krstenja_count"] = s.свештеник_крститељ.count()
        context["vencanja"] = s.свештеник_венчани.select_related(
            "zenik", "nevesta"
        ).order_by("-datum")[:20]
        context["vencanja_count"] = s.свештеник_венчани.count()
        return context


@tenant_role_required("svestenik")
def izmena_svestenika(request, uid):
    """Измена постојеће инстанце."""
    instance = get_object_or_404(Svestenik, uid=uid)
    if request.method == "POST":
        form = SvestenikForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("svestenik_detail", uid=instance.uid)
    else:
        form = SvestenikForm(instance=instance)
    return render(
        request,
        "registar/svestenik.html",
        {
            "form": form,
            "title": "Измена",
            "back_url": reverse("svestenik_detail", kwargs={"uid": instance.uid}),
            "is_edit": True,
            "svestenik": instance,
        },
    )
