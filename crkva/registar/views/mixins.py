"""Заједнички миксини за приказе."""

from django.db import models
from django.db.models.functions import Cast
from registar.forms import SearchForm
from registar.utils import get_query_variants

PAGE_SIZE_CHOICES = [10, 25, 50, 100]
PAGE_SIZE_DEFAULT = 10


class ListControlsMixin:
    """Pagination (per_page) and sorting (sort) for list views.

    Each view declares:
        sort_options = [
            ("prezime", "Презиме А-Ш"),
            ("-prezime", "Презиме Ш-А"),
            ("-created", "Најновије"),
        ]
    """

    sort_options: list[tuple[str, str]] = []

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_size = self.get_paginate_by(self.get_queryset())
        current_sort = self.request.GET.get("sort", "")
        context["page_size_choices"] = PAGE_SIZE_CHOICES
        context["current_page_size"] = current_size
        context["sort_options"] = self.sort_options
        context["current_sort"] = current_sort
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
        if not query:
            ordering = getattr(self, "get_ordering", lambda: None)()
            if ordering:
                queryset = queryset.order_by(*ordering)
            return queryset

        terms = query.split()

        if self.search_date_field:
            queryset = queryset.annotate(
                datum_str=Cast(self.search_date_field, models.CharField())
            )

        combined = models.Q()
        for term in terms:
            variants = get_query_variants(term)
            term_q = models.Q()
            for v in variants:
                for field in self.search_fields:
                    term_q |= models.Q(**{f"{field}__icontains": v})
                if self.search_date_field:
                    term_q |= models.Q(datum_str__icontains=v)
            combined &= term_q

        queryset = queryset.filter(combined).distinct()
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
        partial_template_name = "registar/_stavka_krstenja.html"
    """

    partial_template_name: str | None = None

    def get_template_names(self):
        is_ajax = self.request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax and self.partial_template_name:
            return [self.partial_template_name]
        return super().get_template_names()
