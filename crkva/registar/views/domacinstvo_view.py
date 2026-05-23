"""
Модул за приказ домаћинстава и њихових чланова.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from registar.forms import DomacinstvoForm
from registar.forms.domacinstvo_form import UkucaninFormSet
from registar.models import Domacinstvo
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin
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
        return self.get_search_queryset(
            Domacinstvo.objects.select_related("domacin", "adresa", "slava")
            .prefetch_related("ukucani", "ukucani__osoba")
            .all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for d in context["domacinstva"]:
            members = list(d.ukucani.all())
            d.zivi_clanovi = [u for u in members if not u.preminuo]
            d.preminuli_clanovi = [u for u in members if u.preminuo]
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
        domacinstvo = self.object
        ukucani = domacinstvo.ukucani.all()
        context["ukucani_zivi"] = [u for u in ukucani if not u.preminuo]
        context["ukucani_preminuli"] = [u for u in ukucani if u.preminuo]
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
