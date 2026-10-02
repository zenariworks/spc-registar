"""Јединични тестови за миксине спискова (registar.views.mixins)."""

from unittest import mock

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from registar.views import mixins

AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class FakeListView:
    """Замена за ListView: само куке које миксини позивају преко super()."""

    paginate_by = 10
    ordering = ["prezime"]
    template_name = "spisak.html"

    def __init__(self, request):
        self.request = request
        self.object_list = []

    def get_queryset(self):
        """Празан queryset."""
        return []

    def get_paginate_by(self, queryset):
        """Подразумевана величина стране."""
        return self.paginate_by

    def get_ordering(self):
        """Подразумевано сортирање."""
        return self.ordering

    def get_context_data(self, **kwargs):
        """Почетни контекст."""
        return dict(kwargs)

    def get(self, request, *args, **kwargs):
        """Празан одговор на који миксин може да постави колачић."""
        return HttpResponse()

    def get_template_names(self):
        """Подразумевани шаблон."""
        return [self.template_name]


class ListView(mixins.ListControlsMixin, FakeListView):
    """Списак са контролама за страну, сортирање и приказ."""

    sort_options = [("prezime", "А-Ш"), ("-prezime", "Ш-А")]
    tabela_kolone = ["Име", "Презиме"]


class ScrollView(mixins.ListControlsMixin, mixins.InfiniteScrollMixin, FakeListView):
    """Списак са бесконачним скроловањем."""

    partial_template_name = "_stavka.html"
    partial_template_name_table = "_red.html"


class SearchView(mixins.SearchMixin, ListView):
    """Списак са претрагом."""

    search_fields = ["ime", "prezime"]


def make_view(cls, query="", cookies=None, **headers):
    """Инстанца приказа за GET захтев са задатим упитом и колачићима."""
    request = RequestFactory().get(
        "/spisak/" + ("?" + query if query else ""), **headers
    )
    request.COOKIES.update(cookies or {})
    return cls(request)


class PaginateByTests(SimpleTestCase):
    """Величина стране из ?per_page."""

    def test_allowed_value_is_used(self):
        """Вредност из PAGE_SIZE_CHOICES се поштује."""
        self.assertEqual(make_view(ListView, "per_page=50").get_paginate_by(None), 50)

    def test_value_outside_choices_falls_back(self):
        """Вредност ван понуђених враћа подразумевану."""
        self.assertEqual(make_view(ListView, "per_page=7").get_paginate_by(None), 10)

    def test_non_numeric_falls_back(self):
        """Нечисловна вредност враћа подразумевану."""
        self.assertEqual(make_view(ListView, "per_page=abc").get_paginate_by(None), 10)


class OrderingTests(SimpleTestCase):
    """Сортирање из ?sort."""

    def test_allowed_sort_is_used(self):
        """Понуђено сортирање се примењује."""
        self.assertEqual(
            make_view(ListView, "sort=-prezime").get_ordering(), ["-prezime"]
        )

    def test_unknown_sort_falls_back_to_ordering(self):
        """Непознато сортирање враћа подразумевано."""
        self.assertEqual(
            make_view(ListView, "sort=lozinka").get_ordering(), ["prezime"]
        )


class PrikazTests(SimpleTestCase):
    """Избор приказа картице/табела."""

    def test_default_is_cards(self):
        """Без упита и колачића приказ је картице."""
        self.assertEqual(make_view(ListView).get_prikaz(), "kartice")

    def test_cookie_selects_table(self):
        """Запамћен колачић бира табелу."""
        view = make_view(ListView, cookies={"prikaz": "tabela"})
        self.assertEqual(view.get_prikaz(), "tabela")

    def test_query_overrides_cookie(self):
        """Изричит упит надјачава колачић."""
        view = make_view(ListView, "prikaz=kartice", cookies={"prikaz": "tabela"})
        self.assertEqual(view.get_prikaz(), "kartice")

    def test_invalid_query_is_ignored(self):
        """Непозната вредност упита се занемарује."""
        self.assertEqual(make_view(ListView, "prikaz=mreza").get_prikaz(), "kartice")

    def test_explicit_choice_sets_cookie(self):
        """Изричит избор се памти у колачићу."""
        view = make_view(ListView, "prikaz=tabela")
        response = view.get(view.request)
        self.assertEqual(response.cookies["prikaz"].value, "tabela")
        self.assertEqual(response.cookies["prikaz"]["samesite"], "Lax")

    def test_no_choice_leaves_cookie_alone(self):
        """Без изричитог избора колачић се не поставља."""
        view = make_view(ListView)
        self.assertNotIn("prikaz", view.get(view.request).cookies)


class ListContextTests(SimpleTestCase):
    """Контекст за контроле списка."""

    def test_context_carries_controls(self):
        """Контекст носи изборе и тренутна стања контрола."""
        view = make_view(ListView, "per_page=25&sort=-prezime&prikaz=tabela")
        context = view.get_context_data()
        self.assertEqual(context["page_size_choices"], mixins.PAGE_SIZE_CHOICES)
        self.assertEqual(context["current_page_size"], 25)
        self.assertEqual(context["sort_options"], ListView.sort_options)
        self.assertEqual(context["current_sort"], "-prezime")
        self.assertEqual(context["prikaz"], "tabela")
        self.assertEqual(context["tabela_kolone"], ["Име", "Презиме"])

    def test_toggle_links_keep_query_and_drop_page(self):
        """Везе за промену приказа чувају упит и враћају на прву страну."""
        context = make_view(ListView, "search=ana&page=3").get_context_data()
        self.assertEqual(context["qs_kartice"], "search=ana&prikaz=kartice")
        self.assertEqual(context["qs_tabela"], "search=ana&prikaz=tabela")


class SearchMixinTests(SimpleTestCase):
    """Претрага и сортирање queryset-а."""

    def test_empty_query_only_orders(self):
        """Без упита queryset се само сортира."""
        queryset = mock.Mock()
        with mock.patch.object(mixins, "search_queryset") as search:
            result = make_view(SearchView, "sort=-prezime").get_search_queryset(
                queryset
            )
        search.assert_not_called()
        queryset.order_by.assert_called_once_with("-prezime")
        self.assertIs(result, queryset.order_by.return_value)

    def test_query_is_searched_then_ordered(self):
        """Упит се прослеђује претрази са пољима приказа."""
        queryset = mock.Mock()
        with mock.patch.object(mixins, "search_queryset") as search:
            make_view(SearchView, "search=+ana+").get_search_queryset(queryset)
        search.assert_called_once_with(
            queryset, "ana", ["ime", "prezime"], date_field=None
        )
        search.return_value.order_by.assert_called_once_with("prezime")

    def test_context_has_form_and_query(self):
        """Контекст носи форму и упит."""
        context = make_view(SearchView, "search=ana").get_context_data()
        self.assertEqual(context["upit"], "ana")
        self.assertEqual(context["form"].data["search"], "ana")


class InfiniteScrollTests(SimpleTestCase):
    """Избор шаблона за AJAX бесконачно скроловање."""

    def test_regular_request_uses_full_template(self):
        """Обичан захтев рендерује целу страну."""
        self.assertEqual(make_view(ScrollView).get_template_names(), ["spisak.html"])

    def test_ajax_cards_uses_item_partial(self):
        """AJAX у приказу картица враћа ставке."""
        view = make_view(ScrollView, **AJAX)
        self.assertEqual(view.get_template_names(), ["_stavka.html"])

    def test_ajax_table_uses_row_partial(self):
        """AJAX у табеларном приказу враћа редове."""
        view = make_view(ScrollView, "prikaz=tabela", **AJAX)
        self.assertEqual(view.get_template_names(), ["_red.html"])

    def test_ajax_without_partial_uses_full_template(self):
        """Без партиала и AJAX рендерује целу страну."""
        view = make_view(ScrollView, **AJAX)
        view.partial_template_name = None
        self.assertEqual(view.get_template_names(), ["spisak.html"])
