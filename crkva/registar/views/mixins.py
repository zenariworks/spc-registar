"""Заједнички миксини за приказе."""

from registar.forms import SearchForm
from registar.pretraga import search_queryset

PAGE_SIZE_CHOICES = [10, 25, 50, 100]
PRIKAZI = ("kartice", "tabela")
PRIKAZ_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


class PaginationMixin:
    """Величина стране из `?per_page`, ограничена на PAGE_SIZE_CHOICES."""

    def get_paginate_by(self, queryset):
        try:
            per_page = int(self.request.GET.get("per_page", 0))
        except (ValueError, TypeError):
            per_page = 0
        if per_page in PAGE_SIZE_CHOICES:
            return per_page
        return super().get_paginate_by(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_size_choices"] = PAGE_SIZE_CHOICES
        context["current_page_size"] = self.get_paginate_by(self.object_list)
        return context


class SortMixin:
    """Сортирање из `?sort`, ограничено на понуђене `sort_options`.

    Сваки приказ дефинише:
        sort_options = [
            ("prezime", "Презиме А-Ш"),
            ("-prezime", "Презиме Ш-А"),
            ("-created", "Најновије"),
        ]
    """

    sort_options: list[tuple[str, str]] = []

    def get_ordering(self):
        sort = self.request.GET.get("sort", "")
        allowed = [opt[0] for opt in self.sort_options]
        if sort in allowed:
            return [sort]
        return super().get_ordering() or []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sort_options"] = self.sort_options
        context["current_sort"] = self.request.GET.get("sort", "")
        return context


class PrikazMixin:
    """Приказ картице ↔ табела (#378), запамћен у колачићу.

    Сваки приказ дефинише:
        tabela_kolone = ["Име", "Презиме", ...]  # заглавља за табеларни приказ
    """

    tabela_kolone: list[str] = []

    def get_prikaz(self):
        """Тренутни приказ: „tabela" или „kartice".

        Приоритет: изричит `?prikaz=` из упита, па запамћен избор из колачића
        (последње што је корисник изабрао), па подразумевано „kartice" (#378).
        """
        izbor = self.request.GET.get("prikaz")
        if izbor in PRIKAZI:
            return izbor
        if self.request.COOKIES.get("prikaz") == "tabela":
            return "tabela"
        return "kartice"

    def get(self, request, *args, **kwargs):
        """Памти последњи избор приказа у колачићу кад га корисник изричито мења."""
        response = super().get(request, *args, **kwargs)
        izbor = request.GET.get("prikaz")
        if izbor in PRIKAZI:
            response.set_cookie(
                "prikaz", izbor, max_age=PRIKAZ_COOKIE_MAX_AGE, samesite="Lax"
            )
        return response

    def get_context_data(self, **kwargs):
        """Додаје тренутни приказ и упите за прелаз на други приказ.

        Остали параметри упита се чувају, а `page` се одбацује да би промена
        приказа вратила на прву страну.
        """
        context = super().get_context_data(**kwargs)
        context["prikaz"] = self.get_prikaz()
        context["tabela_kolone"] = self.tabela_kolone
        params = self.request.GET.copy()
        params.pop("page", None)
        for prikaz in PRIKAZI:
            params["prikaz"] = prikaz
            context["qs_" + prikaz] = params.urlencode()
        return context


class ListControlsMixin(PaginationMixin, SortMixin, PrikazMixin):
    """Величина стране, сортирање и приказ картице/табела за спискове."""


class SearchMixin:
    """Јединствена претрага по тексту за све спискове.

    Сваки приказ дефинише:
        search_fields = ["ime", "prezime", "dete__ime", ...]
        search_date_field = "datum"  # опционо, за претрагу по датуму

    Логика:
        - Упит се дели на термине по размацима
        - Сваки термин мора да се пронађе (AND између термина)
        - За сваки термин, све варијанте (лат/ћир) се покушавају (OR)
        - За сваку варијанту, сва поља се претражују (OR)
    """

    search_fields: list[str] = []
    search_date_field: str | None = None

    def get_search_queryset(self, queryset):
        """Филтрира queryset на основу претраге."""
        query = self.request.GET.get("search", "").strip()
        if query:
            queryset = search_queryset(
                queryset,
                query,
                self.search_fields,
                date_field=self.search_date_field,
            )
        ordering = getattr(self, "get_ordering", lambda: None)()
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset

    def get_context_data(self, **kwargs):
        """Додаје форму за претрагу и упит у контекст."""
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm(data=self.request.GET)
        context["upit"] = self.request.GET.get("search", "")
        return context


class InfiniteScrollMixin:
    """Враћа само партиал шаблон када је захтев AJAX (за бесконачно скроловање).

    Сваки приказ дефинише:
        partial_template_name = "_partials/_stavka_krstenja.html"
        partial_template_name_table = "_partials/_red_krstenja.html"  # за prikaz=tabela (#378)
    """

    partial_template_name: str | None = None
    partial_template_name_table: str | None = None

    def get_template_names(self):
        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax:
            prikaz = self.get_prikaz() if hasattr(self, "get_prikaz") else "kartice"
            if prikaz == "tabela" and self.partial_template_name_table:
                return [self.partial_template_name_table]
            if self.partial_template_name:
                return [self.partial_template_name]
        return super().get_template_names()
