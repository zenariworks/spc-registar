"""
Модул за приказ, унос и генерисање PDF докумената за крштења.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView
from registar.forms import KrstenjeForm
from registar.models import Krstenje
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from tenants.permissions import tenant_role_required
from weasyprint import HTML

KRSTENJE_RELATED = (
    "dete",
    "otac",
    "majka",
    "kum",
    "hram",
    "svestenik",
)


@tenant_role_required("krstenje")
def unos_krstenja(request):
    """
    Обрађује захтеве за унос новог крштења. Ако је захтев POST,
    чува податке у базу, иначе приказује формулар за унос.
    """
    if request.method == "POST":
        form = KrstenjeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("krstenja")
    else:
        form = KrstenjeForm()
    return render(
        request,
        "registar/krstenje.html",
        {"form": form, "is_edit": True, "krstenje": None},
    )


class SpisakKrstenja(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак крштења са могућностима претраге и пагинације."""

    model = Krstenje
    template_name = "registar/spisak_krstenja.html"
    partial_template_name = "registar/_stavka_krstenja.html"
    context_object_name = "krstenja"
    paginate_by = 10
    search_fields = [
        "dete__ime",
        "dete__gradjansko_ime",
        "otac__ime",
        "otac__prezime",
        "majka__ime",
        "majka__prezime",
        "kum__ime",
        "kum__prezime",
    ]
    search_date_field = "datum"
    sort_options = [
        ("datum", "Датум растуће"),
        ("-datum", "Датум опадајуће"),
    ]

    def get_queryset(self):
        return self.get_search_queryset(
            Krstenje.objects.select_related(*KRSTENJE_RELATED).order_by("datum")
        )


class KrstenjePDF(LoginRequiredMixin, DetailView):
    """Генерише PDF документ за одређено крштење."""

    model = Krstenje
    template_name = "registar/pdf_krstenje.html"
    context_object_name = "krstenje"

    def get_object(self, queryset=None):
        """Враћа објекат крштења на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(
            Krstenje.objects.select_related(*KRSTENJE_RELATED),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Додаје историјске снимке особа у контекст."""
        context = super().get_context_data(**kwargs)
        from registar.history import history_for

        context["history_entries"] = history_for(self.object)
        krstenje = context["krstenje"]
        event_date = krstenje.datum or krstenje.created

        for role in ["dete", "otac", "majka", "kum"]:
            osoba = getattr(krstenje, role)
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
        response["Content-Disposition"] = f"inline; filename=krstenje-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтеве за генерисање PDF-а."""
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazKrstenja(LoginRequiredMixin, DetailView):
    """Приказује детаљне информације о појединачном крштењу."""

    model = Krstenje
    template_name = "registar/krstenje.html"
    context_object_name = "krstenje"

    def get_object(self) -> Krstenje:
        """Враћа објекат крштења на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(
            Krstenje.objects.select_related(*KRSTENJE_RELATED),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Form bound to instance + is_edit=False so the unified template renders."""
        context = super().get_context_data(**kwargs)
        context["form"] = KrstenjeForm(instance=self.object)
        context["is_edit"] = False
        return context


@tenant_role_required("krstenje")
def calibrate_krstenje(request):
    """Калибрациона страница за подешавање позиција поља на крштеници."""
    return render(request, "registar/calibrate_krstenje.html")


@tenant_role_required("krstenje")
def izmena_krstenja(request, uid):
    """Измена постојеће инстанце."""
    instance = get_object_or_404(Krstenje, uid=uid)
    if request.method == "POST":
        form = KrstenjeForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("krstenje_detail", uid=instance.uid)
    else:
        form = KrstenjeForm(instance=instance)
    return render(
        request,
        "registar/krstenje.html",
        {
            "form": form,
            "is_edit": True,
            "krstenje": instance,
        },
    )
