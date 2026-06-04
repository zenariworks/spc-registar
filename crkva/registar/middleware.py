"""
Middleware за обраду грешака у регистру.
"""

import re

from django.db import ProgrammingError
from django.http import HttpResponse
from django.template import loader

# Регистарске табеле живе само у парохијским (tenant) шемама. Када се захтев
# обрађује над public шемом (нпр. middleware падне на public јер парохија
# није изабрана или шема недостаје), упит над њима баца
# ProgrammingError: relation "..." does not exist. Преводимо познате називе у
# читљиве српске; за непознате користимо сирово име табеле.
TABLE_DISPLAY_NAMES = {
    "krstenja": "крштења",
    "vencanja": "венчања",
    "osobe": "особе",
    "svestenici": "свештеници",
    "domacinstva": "домаћинства",
    "slave": "славе",
    "parohije": "парохије",
    "adrese": "адресе",
    "hramovi": "храмови",
}

_MISSING_RELATION_RE = re.compile(r"relation \"(?P<name>[^\"]+)\" does not exist")


class HandleMissingTablesMiddleware:
    """Middleware који грациозно обрађује грешке када табеле не постоје."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Обради изузетке који се дешавају током обраде захтева.

        Сваки relation "..." does not exist (било која регистарска табела
        недостаје — нпр. domacinstva, slave, … при паду на public) претвара
        у грациозан 503 уместо сировог 500.
        """
        if not isinstance(exception, ProgrammingError):
            return None

        match = _MISSING_RELATION_RE.search(str(exception))
        if not match:
            return None

        raw_name = match.group("name")
        table_name = TABLE_DISPLAY_NAMES.get(raw_name, raw_name)
        template = loader.get_template("registar/missing_table.html")
        context = {
            "table_name": table_name,
            "error_detail": str(exception),
        }
        return HttpResponse(template.render(context, request), status=503)
