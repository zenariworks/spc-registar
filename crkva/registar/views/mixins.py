"""Заједнички миксини за приказе."""

from registar.forms import SearchForm
from registar.search import search_queryset

PAGE_SIZE_CHOICES = [10, 25, 50, 100]
PAGE_SIZE_DEFAULT = 10


class ListControlsMixin:
    """Pagination (per_page), sorting (sort) and card/table view (prikaz) for list views.

    Each view declares:
        sort_options = [
            ("prezime", "Презиме А-Ш"),
            ("-prezime", "Презиме Ш-А"),
            ("-created", "Најновије"),
        ]
        tabela_kolone = ["Име", "Презиме", ...]  # заглавља за табеларни приказ (#378)
    """

    sort_options: list[tuple[str, str]] = []
    tabela_kolone: list[str] = []

    def get_paginate_by(self, queryset):
        try:
            per_page = int(self.request.GET.get("per_page", 0))
        except (ValueError, TypeError):
            per_page = 0
        if per_page in PAGE_SIZE_CHOICES:
            return per_page
        return super().get_paginate_by(queryset)

    def get_ordering(self):
        sort = self.request.GET.get("sort", "")
        allowed = [opt[0] for opt in self.sort_options]
        if sort in allowed:
            return [sort]
        return super().get_ordering() or []

    def get_prikaz(self):
        """Тренутни приказ: „tabela" или „kartice" (подразумевано)."""
        return "tabela" if self.request.GET.get("prikaz") == "tabela" else "kartice"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_size = self.get_paginate_by(self.get_queryset())
        current_sort = self.request.GET.get("sort", "")
        context["page_size_choices"] = PAGE_SIZE_CHOICES
        context["current_page_size"] = current_size
        context["sort_options"] = self.sort_options
        context["current_sort"] = current_sort

        # Приказ картице ↔ табела (#378). Чувамо остале параметре упита; `page`
        # одбацујемо да пребацивање приказа врати на прву страну.
        context["prikaz"] = self.get_prikaz()
        context["tabela_kolone"] = self.tabela_kolone
        params = self.request.GET.copy()
        params.pop("page", None)
        params["prikaz"] = "kartice"
        context["qs_kartice"] = params.urlencode()
        params["prikaz"] = "tabela"
        context["qs_tabela"] = params.urlencode()
        return context


# Keep old name as alias
PageSizeMixin = ListControlsMixin


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
            if (
                self.request.GET.get("prikaz") == "tabela"
                and self.partial_template_name_table
            ):
                return [self.partial_template_name_table]
            if self.partial_template_name:
                return [self.partial_template_name]
        return super().get_template_names()
