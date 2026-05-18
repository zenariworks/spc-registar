"""
Модул за приказ, додавање и генерисање PDF докумената за парохијане.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from registar.forms import ParohijanForm
from registar.models import Krstenje
from registar.models.parohijan import Parohijan
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from tenants.permissions import tenant_role_required
from weasyprint import HTML


@tenant_role_required("osoba")
def unos_parohijana(request):
    """
    Обрађује захтев за додавање новог парохијана. Ако је метод POST,
    подаци се чувају у базу. У супротном, приказује се формулар за унос.
    """
    if request.method == "POST":
        form = ParohijanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("parohijani")
    else:
        form = ParohijanForm()
    return render(
        request,
        "registar/parohijan.html",
        {"form": form, "is_edit": True, "parohijan": None},
    )


class SpisakParohijana(SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView):
    """Приказује списак парохијана са могућношћу претраге и пагинације."""

    model = Parohijan
    template_name = "registar/spisak_parohijana.html"
    partial_template_name = "registar/_stavka_parohijana.html"
    context_object_name = "parohijani"
    paginate_by = 10
    ordering = ["prezime", "ime"]
    search_fields = ["ime", "prezime"]
    sort_options = [
        ("prezime", "Презиме А-Ш"),
        ("-prezime", "Презиме Ш-А"),
        ("ime", "Име А-Ш"),
        ("-created", "Најновије"),
    ]

    def get_queryset(self):
        from django.db.models import Prefetch
        from registar.models import Ukucanin

        ukucanin_qs = Ukucanin.objects.select_related(
            "domacinstvo", "domacinstvo__domacin", "domacinstvo__adresa"
        )
        return self.get_search_queryset(
            Parohijan.objects.filter(parohijan=True)
            .select_related("adresa")
            .select_related("domacinstvo", "domacinstvo__adresa")
            .prefetch_related(
                Prefetch(
                    "ukucanin_set",
                    queryset=ukucanin_qs,
                    to_attr="prefetched_ukucanstva",
                )
            )
            .all()
        )


class ParohijanPDF(DetailView):
    """Генерише PDF документ за одређеног парохијана."""

    model = Parohijan
    template_name = "registar/pdf_parohijan.html"

    def get_object(self, queryset=None):
        """Преузима парохијана на основу UID-а."""
        uid = self.kwargs.get("uid")
        return get_object_or_404(Parohijan, uid=uid)

    def render_to_response(self, context, **response_kwargs):
        """Претвара HTML садржај у PDF и враћа HTTP одговор са PDF документом."""
        html_string = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(
            string=html_string, base_url=self.request.build_absolute_uri()
        ).write_pdf()
        uid = self.kwargs.get("uid")
        response = HttpResponse(content=pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"inline; filename=parohijan-{uid}.pdf"
        return response

    def get(self, request, *args, **kwargs):
        """Обрађује GET захтев за генерисање PDF документа за парохијана."""
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PrikazParohijana(DetailView):
    """Приказује детаљне информације о одређеном парохијану."""

    model = Parohijan
    template_name = "registar/parohijan.html"
    context_object_name = "parohijan"
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        """Преузима парохијана на основу UID-а."""
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(Parohijan, uid=uid)

    def get_context_data(self, **kwargs):
        from registar.history import history_for

        context = super().get_context_data(**kwargs)
        context["history_entries"] = history_for(self.object)
        context["form"] = ParohijanForm(instance=self.object)
        context["is_edit"] = False
        p = self.object

        # Крштења
        context["krstenja_dete"] = p.krstenja_kao_dete.select_related(
            "otac", "majka", "kum"
        ).all()
        context["krstenja_kum"] = p.krstenja_kao_kum.select_related("dete").all()

        # Венчања
        context["vencanja_zenik"] = p.vencanja_kao_zenik.select_related("nevesta").all()
        context["vencanja_nevesta"] = p.vencanja_kao_nevesta.select_related(
            "zenik"
        ).all()
        context["vencanja_kum"] = p.vencanja_kao_kum.select_related(
            "zenik", "nevesta"
        ).all()

        # Венчања — родитељи и старосват
        roditelj_sel = ("zenik", "nevesta")
        context["vencanja_svekar"] = p.vencanja_kao_svekar.select_related(
            *roditelj_sel
        ).all()
        context["vencanja_svekrva"] = p.vencanja_kao_svekrva.select_related(
            *roditelj_sel
        ).all()
        context["vencanja_tast"] = p.vencanja_kao_tast.select_related(
            *roditelj_sel
        ).all()
        context["vencanja_tasta"] = p.vencanja_kao_tasta.select_related(
            *roditelj_sel
        ).all()
        context["vencanja_stari_svat"] = p.vencanja_kao_stari_svat.select_related(
            *roditelj_sel
        ).all()

        # Крштења — родитељи (где је ова особа отац или мајка)
        context["krstenja_otac"] = p.krstenja_kao_otac.select_related(
            "dete", "majka"
        ).all()
        context["krstenja_majka"] = p.krstenja_kao_majka.select_related(
            "dete", "otac"
        ).all()

        # Родитељи (из крштења где је ова особа дете)
        krstenje_kao_dete = p.krstenja_kao_dete.select_related("otac", "majka").first()
        if krstenje_kao_dete:
            context["otac"] = krstenje_kao_dete.otac
            context["majka"] = krstenje_kao_dete.majka

        # Деца (из крштења где је ова особа отац или мајка)
        deca_kao_otac = Krstenje.objects.filter(otac=p).select_related("dete")
        deca_kao_majka = Krstenje.objects.filter(majka=p).select_related("dete")
        deca = []
        seen = set()
        for k in list(deca_kao_otac) + list(deca_kao_majka):
            if k.dete and k.dete.uid not in seen:
                deca.append(k.dete)
                seen.add(k.dete.uid)
        context["deca"] = deca

        # Домаћинство (као укућанин)
        from registar.models import Ukucanin

        context["ukucanstva"] = Ukucanin.objects.filter(osoba=p).select_related(
            "domacinstvo", "domacinstvo__domacin"
        )

        return context


@tenant_role_required("osoba")
def izmena_parohijana(request, uid):
    """Измена постојеће инстанце."""
    instance = get_object_or_404(Parohijan, uid=uid)
    if request.method == "POST":
        form = ParohijanForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("parohijan_detail", uid=instance.uid)
    else:
        form = ParohijanForm(instance=instance)
    return render(
        request,
        "registar/parohijan.html",
        {
            "form": form,
            "title": "Измена",
            "back_url": reverse("parohijan_detail", kwargs={"uid": instance.uid}),
            "is_edit": True,
            "parohijan": instance,
        },
    )
