"""
Модул за приказ домаћинстава и њихових чланова.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView
from registar.forms import DomacinstvoForm
from registar.forms.domacinstvo import UkucaninFormSet
from registar.models import Domacinstvo, Svestenik
from registar.views.base import EditChromeMixin, RegistarCreateView, RegistarUpdateView
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
from registar.views.spiskovi import grupisi_po_ulici, razdvoji_zive_i_preminule
from registar.views.territory import by_parish_filter, resolve_svestenik


class DomacinstvoCreate(RegistarCreateView):
    """Унос новог домаћинства (без inline формсета)."""

    form_class = DomacinstvoForm
    template_name = "registar/domacinstvo.html"
    context_object_name = "domacinstvo"
    role = "domacinstvo"
    success_url_name = "domacinstva"


unos_domacinstva = DomacinstvoCreate.as_view()


class SpisakDomacinsta(
    LoginRequiredMixin, SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView
):
    """Приказује списак домаћинстава са могућношћу претраге и пагинације."""

    model = Domacinstvo
    template_name = "registar/spisak_domacinstva.html"
    partial_template_name = "_partials/_stavka_domacinstva.html"
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
            d.zivi_clanovi, d.preminuli_clanovi = razdvoji_zive_i_preminule(
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
            razdvoji_zive_i_preminule(self.object.ukucani.all())
        )
        return context


class DomacinstvoUpdate(EditChromeMixin, RegistarUpdateView):
    """Измена домаћинства са inline формсетом укућана.

    Формсет се везује из POST-а само када је његов management form
    заиста присутан (рендерује се тек у edit-моду inline toggle-а),
    исто као стари FBV.
    """

    model = Domacinstvo
    form_class = DomacinstvoForm
    template_name = "registar/domacinstvo.html"
    context_object_name = "domacinstvo"
    role = "domacinstvo"
    detail_url_name = "domacinstvo_detail"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("ukucanin_formset", UkucaninFormSet(instance=self.object))
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        has_formset = "ukucani-TOTAL_FORMS" in request.POST
        if has_formset:
            formset = UkucaninFormSet(request.POST, instance=self.object)
        else:
            formset = UkucaninFormSet(instance=self.object)
        if form.is_valid() and (not has_formset or formset.is_valid()):
            form.save()
            if has_formset:
                formset.save()
            return HttpResponseRedirect(self.get_success_url())
        return self.render_to_response(
            self.get_context_data(form=form, ukucanin_formset=formset)
        )


izmena_domacinstva = DomacinstvoUpdate.as_view()


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

    grupe = grupisi_po_ulici(domacinstva)
    return render(
        request,
        "registar/domacinstva_print.html",
        {
            "svestenik": svestenik,
            "grupe": grupe,
            "ukupno": len(domacinstva),
        },
    )
