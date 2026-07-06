"""
Модул за приказ домаћинстава и њихових чланова.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from registar.forms import DomacinstvoForm
from registar.forms.domacinstvo_form import UkucaninFormSet
from registar.models import Domacinstvo, Svestenik
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from registar.views.roster import group_by_street, partition_zivi_preminuli
from registar.views.territory import by_parish_filter, resolve_svestenik
from tenants.permissions import tenant_role_required


@tenant_role_required("domacinstvo")
def unos_domacinstva(request):
    """Обрађује захтев за додавање новог домаћинства."""
    if request.method == "POST":
        form = DomacinstvoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("domacinstva")
    else:
        form = DomacinstvoForm()
    return render(
        request,
        "registar/domacinstvo.html",
        {"form": form, "is_edit": True, "domacinstvo": None},
    )


class SpisakDomacinsta(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак домаћинстава са могућношћу претраге и пагинације."""

    model = Domacinstvo
    template_name = "registar/spisak_domacinstva.html"
    partial_template_name = "registar/_stavka_domacinstva.html"
    context_object_name = "domacinstva"
    paginate_by = 20
    search_fields = ["domacin__ime", "domacin__prezime", "adresa__ulica"]
    sort_options = [
        ("adresa__ulica", "Адреса А-Ш"),
        ("-adresa__ulica", "Адреса Ш-А"),
        ("domacin__prezime", "Презиме А-Ш"),
        ("-domacin__prezime", "Презиме Ш-А"),
    ]
    ordering = ["adresa__ulica", "adresa__broj", "domacin__prezime", "domacin__ime"]

    def get_queryset(self):
        qs = (
            Domacinstvo.objects.select_related(
                "domacin", "adresa", "adresa__svestenik", "slava"
            )
            .prefetch_related("ukucani", "ukucani__osoba")
            .all()
        )
        qs = by_parish_filter(qs, resolve_svestenik(self.request))
        return self.get_search_queryset(qs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for d in context["domacinstva"]:
            d.zivi_clanovi, d.preminuli_clanovi = partition_zivi_preminuli(
                d.ukucani.all()
            )
        # Priest filter controls (issue #26).
        svestenik = resolve_svestenik(self.request)
        context["svestenik_filter_options"] = Svestenik.objects.order_by(
            "prezime", "ime"
        )
        context["current_svestenik"] = (self.request.GET.get("svestenik") or "").strip()
        context["selected_svestenik"] = svestenik
        return context


class PrikazDomacinstva(LoginRequiredMixin, DetailView):
    """Приказује детаљне информације о одређеном домаћинству."""

    model = Domacinstvo
    template_name = "registar/domacinstvo.html"
    context_object_name = "domacinstvo"
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        """Преузима домаћинство на основу UID-а."""
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(
            Domacinstvo.objects.select_related(
                "domacin", "adresa", "slava"
            ).prefetch_related("ukucani", "ukucani__osoba"),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Додаје укућане у контекст."""
        from registar.history import history_for

        context = super().get_context_data(**kwargs)
        context["history_entries"] = history_for(self.object)
        context["domacinstvo"] = self.object
        context["is_edit"] = False
        context["form"] = DomacinstvoForm(instance=self.object)
        context["ukucanin_formset"] = UkucaninFormSet(instance=self.object)
        context["ukucani_zivi"], context["ukucani_preminuli"] = (
            partition_zivi_preminuli(self.object.ukucani.all())
        )
        return context


@tenant_role_required("domacinstvo")
def izmena_domacinstva(request, uid):
    """Измена постојеће инстанце."""
    instance = get_object_or_404(Domacinstvo, uid=uid)
    if request.method == "POST":
        form = DomacinstvoForm(request.POST, instance=instance)
        # The Ukucanin formset is only bound when the management form is
        # actually present in the POST (the formset is rendered only in
        # edit-mode of the inline edit toggle).
        has_formset = "ukucani-TOTAL_FORMS" in request.POST
        if has_formset:
            ukucanin_formset = UkucaninFormSet(request.POST, instance=instance)
        else:
            ukucanin_formset = UkucaninFormSet(instance=instance)
        if form.is_valid() and (not has_formset or ukucanin_formset.is_valid()):
            form.save()
            if has_formset:
                ukucanin_formset.save()
            return redirect("domacinstvo_detail", uid=instance.uid)
    else:
        form = DomacinstvoForm(instance=instance)
        ukucanin_formset = UkucaninFormSet(instance=instance)
    return render(
        request,
        "registar/domacinstvo.html",
        {
            "form": form,
            "ukucanin_formset": ukucanin_formset,
            "title": "Измена",
            "back_url": reverse("domacinstvo_detail", kwargs={"uid": instance.uid}),
            "is_edit": True,
            "domacinstvo": instance,
        },
    )


@login_required
def domacinstva_print(request: HttpRequest) -> HttpResponse:
    """Штампа домаћинстава изабраног свештеника, груписано по улици (#26).

    За разлику од листе са бесконачним скроловањем, овде се рендерују СВА
    домаћинства парохије изабраног свештеника (адреса + телефони), погодно за
    обилазак на терену.
    """
    svestenik = resolve_svestenik(request)
    domacinstva = []
    if svestenik is not None and svestenik.parohija_id:
        domacinstva = list(
            by_parish_filter(
                Domacinstvo.objects.select_related(
                    "domacin", "adresa", "adresa__svestenik"
                ),
                svestenik,
            ).order_by(
                "adresa__ulica", "adresa__broj", "domacin__prezime", "domacin__ime"
            )
        )

    grupe = group_by_street(domacinstva)
    return render(
        request,
        "registar/domacinstva_print.html",
        {
            "svestenik": svestenik,
            "grupe": grupe,
            "ukupno": len(domacinstva),
        },
    )
