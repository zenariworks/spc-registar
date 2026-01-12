"""
Модул за приказ домаћинстава и њихових чланова.
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from registar.forms import SearchForm
from registar.models import Domacinstvo
from registar.utils import get_query_variants


class SpisakDomacinsta(ListView):
    """Приказује списак домаћинстава са могућношћу претраге и пагинације."""

    model = Domacinstvo
    template_name = "registar/spisak_domacinstva.html"
    context_object_name = "domacinstva"
    paginate_by = 20

    def get_queryset(self):
        """Филтрира домаћинства на основу унетог појма у форми за претрагу."""
        form = SearchForm(data=self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get("search", "")
            if not query:
                return (
                    Domacinstvo.objects.select_related(
                        "domacin", "adresa", "adresa__ulica", "slava"
                    )
                    .prefetch_related("ukucani", "ukucani__osoba")
                    .all()
                )
            variants = get_query_variants(query)
            q = None
            for v in variants:
                clause = (
                    Q(domacin__ime__icontains=v)
                    | Q(domacin__prezime__icontains=v)
                    | Q(adresa__ulica__naziv__icontains=v)
                )
                q = clause if q is None else (q | clause)
            return (
                Domacinstvo.objects.select_related(
                    "domacin", "adresa", "adresa__ulica", "slava"
                )
                .prefetch_related("ukucani", "ukucani__osoba")
                .filter(q)
                if q is not None
                else Domacinstvo.objects.select_related(
                    "domacin", "adresa", "adresa__ulica", "slava"
                )
                .prefetch_related("ukucani", "ukucani__osoba")
                .all()
            )
        return (
            Domacinstvo.objects.select_related(
                "domacin", "adresa", "adresa__ulica", "slava"
            )
            .prefetch_related("ukucani", "ukucani__osoba")
            .all()
        )

    def get_context_data(self, **kwargs):
        """Додаје форму за претрагу у контекст шаблона."""
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(data=self.request.GET)
        context["upit"] = self.request.GET.get("search", "")
        return context


class PrikazDomacinstva(DetailView):
    """Приказује детаљне информације о одређеном домаћинству."""

    model = Domacinstvo
    template_name = "registar/info_domacinstvo.html"
    context_object_name = "domacinstvo"
    pk_url_kwarg = "uid"

    def get_object(self, queryset=None):
        """Преузима домаћинство на основу UID-а."""
        uid = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(
            Domacinstvo.objects.select_related(
                "domacin", "adresa", "adresa__ulica", "slava"
            ).prefetch_related("ukucani", "ukucani__osoba"),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Додаје укућане у контекст."""
        context = super().get_context_data(**kwargs)
        domacinstvo = self.object
        # Separate active and deceased ukucani
        ukucani = domacinstvo.ukucani.all()
        context["ukucani_zivi"] = [u for u in ukucani if not u.preminuo]
        context["ukucani_preminuli"] = [u for u in ukucani if u.preminuo]
        return context
