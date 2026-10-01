"""Заједничка логика претраге по тексту.

Један извор истине за претрагу: упит се дели на термине, за сваки термин се
пробају латиничне/ћириличне варијанте (види :func:`get_query_variants`) и
претражују задата поља (преко релационих путања), уз опциону претрагу по
датуму. Користе је и спискови (:class:`SearchMixin`) и глобална претрага
(``search_view``/``search_autocomplete``), па се алгоритам не дуплира.
"""

from django.db import models
from django.db.models.functions import Cast
from registar.utils import get_query_variants


def build_search_q(query, fields, *, split_terms=True, date_alias=None):
    """Гради ``Q`` за претрагу преко ``fields``.

    - ``split_terms=True``: упит се дели по размацима, сваки термин мора да се
      пронађе (AND), а унутар термина се OR-ује преко (варијанте × поља).
    - ``split_terms=False``: цео упит се третира као један термин.
    - ``date_alias``: ако је дато, додаје OR на тај анотирани алиас (нпр.
      ``"datum_str"``); анотацију обезбеђује позивалац / :func:`search_queryset`.
    """
    query = (query or "").strip()
    if not query:
        return models.Q()

    terms = query.split() if split_terms else [query]
    combined = models.Q()
    for term in terms:
        term_q = models.Q()
        for variant in get_query_variants(term):
            for field in fields:
                term_q |= models.Q(**{f"{field}__icontains": variant})
            if date_alias:
                term_q |= models.Q(**{f"{date_alias}__icontains": variant})
        combined &= term_q
    return combined


def search_queryset(queryset, query, fields, *, date_field=None):
    """Филтрира ``queryset`` претрагом по тексту (термин-сплит + датум).

    Када је ``date_field`` задат, поље се кастује у текст ради ``icontains``
    претраге по датуму (нпр. „2024-05-17“). Резултат је ``distinct``.
    """
    query = (query or "").strip()
    if not query:
        return queryset

    date_alias = None
    if date_field:
        date_alias = "datum_str"
        queryset = queryset.annotate(
            **{date_alias: Cast(date_field, models.CharField())}
        )

    q = build_search_q(query, fields, date_alias=date_alias)
    return queryset.filter(q).distinct()
