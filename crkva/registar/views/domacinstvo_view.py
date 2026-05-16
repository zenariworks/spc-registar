"""
Модул за приказ домаћинстава и њихових чланова.
"""

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView
from registar.models import Domacinstvo
from registar.views.mixins import InfiniteScrollMixin, PageSizeMixin, SearchMixin


class SpisakDomacinsta(SearchMixin, PageSizeMixin, InfiniteScrollMixin, ListView):
    """Приказује списак домаћинстава са могућношћу претраге и пагинације."""

    model = Domacinstvo
    template_name = "registar/spisak_domacinstva.html"
    partial_template_name = "registar/_stavka_domacinstva.html"
    context_object_name = "domacinstva"
    paginate_by = 20
    search_fields = ["domacin__ime", "domacin__prezime", "adresa__ulica"]
    sort_options = [
        ("domacin__prezime", "Презиме А-Ш"),
        ("-domacin__prezime", "Презиме Ш-А"),
    ]
    ordering = ["domacin__prezime", "domacin__ime"]

    def get_queryset(self):
        return self.get_search_queryset(
            Domacinstvo.objects.select_related("domacin", "adresa", "slava")
            .prefetch_related("ukucani", "ukucani__osoba")
            .all()
        )


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
                "domacin", "adresa", "slava"
            ).prefetch_related("ukucani", "ukucani__osoba"),
            uid=uid,
        )

    def get_context_data(self, **kwargs):
        """Додаје укућане у контекст."""
        context = super().get_context_data(**kwargs)
        domacinstvo = self.object
        ukucani = domacinstvo.ukucani.all()
        context["ukucani_zivi"] = [u for u in ukucani if not u.preminuo]
        context["ukucani_preminuli"] = [u for u in ukucani if u.preminuo]
        return context
