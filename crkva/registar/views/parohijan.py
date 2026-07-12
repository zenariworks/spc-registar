"""
Модул за приказ, додавање и генерисање PDF докумената за парохијане.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from registar.forms import ParohijanForm
from registar.models import Krstenje
from registar.models.parohijan import Osoba
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from registar.views.pdf import HistorySnapshotMixin, PdfDetailView
from tenants.permissions import tenant_role_required


@tenant_role_required("osoba")
def unos_parohijana(request):
    """
    Обрађује захтев за додавање новог парохијана. Ако је метод POST,
    подаци се чувају у базу. У супротном, приказује се формулар за унос.
    """
    if request.method == "POST":
        form = ParohijanForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.parohijan = True
            obj.save()
            form.save_m2m()
            return redirect("parohijani")
    else:
        form = ParohijanForm()
    return render(
        request,
        "registar/parohijan.html",
        {"form": form, "is_edit": True, "parohijan": None},
    )


class SpisakParohijana(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак парохијана са могућношћу претраге и пагинације."""

    model = Osoba
    template_name = "registar/spisak_parohijana.html"
    partial_template_name = "_partials/_stavka_parohijana.html"
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
            Osoba.objects.filter(parohijan=True)
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


class ParohijanPDF(HistorySnapshotMixin, PdfDetailView):
    """Генерише PDF документ за одређеног парохијана."""

    model = Osoba
    template_name = "registar/pdf_parohijan.html"
    filename_prefix = "parohijan"


class PrikazParohijana(LoginRequiredMixin, DetailView):
    """Приказује детаљне информације о одређеном парохијану."""

    model = Osoba
    template_name = "registar/parohijan.html"
    context_object_name = "parohijan"
    pk_url_kwarg = "uid"

    def get_queryset(self):
        """Prefetch every Krstenje / Vencanje / Ukucanin relation the
        detail template touches so the whole page is a fixed cost (one
        SELECT per relation + the parent), independent of how many rows
        this parohijan has in each role. Without this the template fires
        15+ separate queries per render."""
        from django.db.models import Prefetch
        from registar.models import Ukucanin, Vencanje

        return Osoba.objects.prefetch_related(
            Prefetch(
                "krstenja_kao_dete",
                queryset=Krstenje.objects.select_related("otac", "majka", "kum"),
            ),
            Prefetch(
                "krstenja_kao_kum", queryset=Krstenje.objects.select_related("dete")
            ),
            Prefetch(
                "krstenja_kao_otac",
                queryset=Krstenje.objects.select_related("dete", "majka"),
            ),
            Prefetch(
                "krstenja_kao_majka",
                queryset=Krstenje.objects.select_related("dete", "otac"),
            ),
            Prefetch(
                "vencanja_kao_zenik",
                queryset=Vencanje.objects.select_related("nevesta"),
            ),
            Prefetch(
                "vencanja_kao_nevesta",
                queryset=Vencanje.objects.select_related("zenik"),
            ),
            Prefetch(
                "vencanja_kao_kum",
                queryset=Vencanje.objects.select_related("zenik", "nevesta"),
            ),
            Prefetch(
                "vencanja_kao_svekar",
                queryset=Vencanje.objects.select_related("zenik", "nevesta"),
            ),
            Prefetch(
                "vencanja_kao_svekrva",
                queryset=Vencanje.objects.select_related("zenik", "nevesta"),
            ),
            Prefetch(
                "vencanja_kao_tast",
                queryset=Vencanje.objects.select_related("zenik", "nevesta"),
            ),
            Prefetch(
                "vencanja_kao_tasta",
                queryset=Vencanje.objects.select_related("zenik", "nevesta"),
            ),
            Prefetch(
                "vencanja_kao_stari_svat",
                queryset=Vencanje.objects.select_related("zenik", "nevesta"),
            ),
            Prefetch(
                "ukucanin_set",
                queryset=Ukucanin.objects.select_related(
                    "domacinstvo", "domacinstvo__domacin"
                ),
            ),
        )

    def get_object(self, queryset=None):
        """Преузима парохијана на основу UID-а."""
        uid = self.kwargs.get(self.pk_url_kwarg)
        qs = queryset if queryset is not None else self.get_queryset()
        return get_object_or_404(qs, uid=uid)

    def get_context_data(self, **kwargs):
        from registar.history import history_for

        context = super().get_context_data(**kwargs)
        context["history_entries"] = history_for(self.object)
        context["form"] = ParohijanForm(instance=self.object)
        context["is_edit"] = False
        p = self.object

        # All collections below hit the prefetched cache from get_queryset().
        krstenja_dete = list(p.krstenja_kao_dete.all())
        krstenja_otac = list(p.krstenja_kao_otac.all())
        krstenja_majka = list(p.krstenja_kao_majka.all())
        context["krstenja_dete"] = krstenja_dete
        context["krstenja_kum"] = list(p.krstenja_kao_kum.all())
        context["krstenja_otac"] = krstenja_otac
        context["krstenja_majka"] = krstenja_majka

        context["vencanja_zenik"] = list(p.vencanja_kao_zenik.all())
        context["vencanja_nevesta"] = list(p.vencanja_kao_nevesta.all())
        context["vencanja_kum"] = list(p.vencanja_kao_kum.all())
        context["vencanja_svekar"] = list(p.vencanja_kao_svekar.all())
        context["vencanja_svekrva"] = list(p.vencanja_kao_svekrva.all())
        context["vencanja_tast"] = list(p.vencanja_kao_tast.all())
        context["vencanja_tasta"] = list(p.vencanja_kao_tasta.all())
        context["vencanja_stari_svat"] = list(p.vencanja_kao_stari_svat.all())

        # Родитељи: reuse the first Krstenje where this person is the дете.
        if krstenja_dete:
            context["otac"] = krstenja_dete[0].otac
            context["majka"] = krstenja_dete[0].majka

        # Деца: dedup across krstenja_kao_otac + krstenja_kao_majka. Reuse
        # the already-loaded rows instead of re-querying Krstenje.
        deca, seen = [], set()
        for k in krstenja_otac + krstenja_majka:
            if k.dete and k.dete.uid not in seen:
                deca.append(k.dete)
                seen.add(k.dete.uid)
        context["deca"] = deca

        # Домаћинства (member-of). Prefetched via ukucanin_set above.
        context["ukucanstva"] = list(p.ukucanin_set.all())

        return context


@tenant_role_required("osoba")
def izmena_parohijana(request, uid):
    """Измена постојеће инстанце."""
    parohijan = get_object_or_404(Osoba, uid=uid)
    if request.method == "POST":
        form = ParohijanForm(request.POST, instance=parohijan)
        if form.is_valid():
            # Force parohijan=True on edit too — mirror unos_parohijana so
            # editing a person via this view never silently drops the flag.
            obj = form.save(commit=False)
            obj.parohijan = True
            obj.save()
            form.save_m2m()
            return redirect("parohijan_detail", uid=parohijan.uid)
    else:
        form = ParohijanForm(instance=parohijan)
    return render(
        request,
        "registar/parohijan.html",
        {
            "form": form,
            "title": "Измена",
            "back_url": reverse("parohijan_detail", kwargs={"uid": parohijan.uid}),
            "is_edit": True,
            "parohijan": parohijan,
        },
    )
