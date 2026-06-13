"""
Модул за приказ, унос, претрагу и генерисање PDF докумената за венчања.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView
from registar.forms import VencanjeForm
from registar.models.vencanje import Vencanje
from registar.services.izdavalac import get_izdavalac
from registar.views.calibrate_view import render_calibrate
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from tenants.permissions import tenant_role_required
from weasyprint import HTML

VENCANJE_RELATED = (
    "zenik",
    "nevesta",
    "kum",
    "svekar",
    "svekrva",
    "tast",
    "tasta",
    "stari_svat",
    "hram",
    "svestenik",
)


class SpisakVencanja(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак венчања са могућностима претраге и пагинације."""

    model = Vencanje
    template_name = "registar/spisak_vencanja.html"
    partial_template_name = "registar/_stavka_vencanja.html"
    context_object_name = "vencanja"
    paginate_by = 10
    search_fields = [
        "zenik__ime",
        "zenik__prezime",
        "nevesta__ime",
        "nevesta__prezime",
        "kum__ime",
        "stari_svat__ime",
        "hram__naziv",
    ]
    search_date_field = "datum"
    sort_options = [
        ("datum", "Датум растуће"),
        ("-datum", "Датум опадајуће"),
    ]

    def get_queryset(self):
        return self.get_search_queryset(
            Vencanje.objects.select_related(*VENCANJE_RELATED).order_by("datum")
        )


class VencanjePDF(LoginRequiredMixin, DetailView):
    """Генерише PDF документ за одређено венчање."""

    model = Vencanje
    template_name = "registar/pdf_vencanje.html"
    context_object_name = "vencanje"

    def get_object(self, queryset=None):
        """Враћа објекат венчања на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(
            Vencanje.objects.select_related(*VENCANJE_RELATED),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Додаје историјске снимке особа у контекст."""
        context = super().get_context_data(**kwargs)
        from registar.history import history_for

        context["history_entries"] = history_for(self.object)
        vencanje = context["vencanje"]
        event_date = vencanje.datum or vencanje.created

        for role in [
            "zenik",
            "nevesta",
            "kum",
            "svekar",
            "svekrva",
            "tast",
            "tasta",
            "stari_svat",
        ]:
            osoba = getattr(vencanje, role)
            if osoba:
                try:
                    historical = osoba.history.as_of(event_date)
                    context[f"{role}_snapshot"] = historical
                except type(osoba).DoesNotExist:
                    context[f"{role}_snapshot"] = osoba
            else:
                context[f"{role}_snapshot"] = None

        return context

    def render_to_response(self, context, **response_kwargs):
        """Претвара HTML садржај у PDF и враћа HTTP одговор са PDF документом."""
        html = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(string=html, base_url=self.request.build_absolute_uri()).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=vencanje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтеве за генерисање PDF-а."""
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazVencanja(LoginRequiredMixin, DetailView):
    """Приказује детаљне информације о појединачном венчању."""

    model = Vencanje
    template_name = "registar/vencanje.html"
    context_object_name = "vencanje"

    def get_object(self) -> Vencanje:
        """Враћа објекат венчања на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(
            Vencanje.objects.select_related(*VENCANJE_RELATED),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Form bound to instance + is_edit=False so the unified template renders."""
        context = super().get_context_data(**kwargs)
        context["form"] = VencanjeForm(instance=self.object)
        context["is_edit"] = False
        context["izdavalac"] = get_izdavalac(self.request)
        return context


@tenant_role_required("vencanje")
def unos_vencanja(request):
    """Обрада уноса новог венчања."""
    if request.method == "POST":
        form = VencanjeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("vencanja")
    else:
        form = VencanjeForm()
    return render(
        request,
        "registar/vencanje.html",
        {"form": form, "is_edit": True, "vencanje": None},
    )


@tenant_role_required("vencanje")
def calibrate_vencanje(request):
    """Приказује страницу за калибрацију позиција поља на венчаници."""
    return render_calibrate(request, "vencanje")


@tenant_role_required("vencanje")
def izmena_vencanja(request, uid):
    """Измена постојеће инстанце."""
    instance = get_object_or_404(Vencanje, uid=uid)
    if request.method == "POST":
        form = VencanjeForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("vencanje_detail", uid=instance.uid)
    else:
        form = VencanjeForm(instance=instance)
    return render(
        request,
        "registar/vencanje.html",
        {
            "form": form,
            "is_edit": True,
            "vencanje": instance,
        },
    )
