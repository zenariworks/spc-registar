"""
Middleware за обраду грешака у регистру.
"""

from django.db import ProgrammingError
from django.http import HttpResponse
from django.template import loader


class HandleMissingTablesMiddleware:
    """Middleware који грациозно обрађује грешке када табеле не постоје."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Обради изузетке који се дешавају током обраде захтева."""
        if isinstance(exception, ProgrammingError):
            error_message = str(exception)
            if "relation" in error_message and "does not exist" in error_message:
                # Извуци име табеле из поруке о грешци
                table_name = None
                if '"krstenja"' in error_message:
                    table_name = "крштења"
                elif '"vencanja"' in error_message:
                    table_name = "венчања"
                elif '"osobe"' in error_message:
                    table_name = "особе"
                elif '"svestenici"' in error_message:
                    table_name = "свештеници"

                if table_name:
                    template = loader.get_template("registar/missing_table.html")
                    context = {
                        "table_name": table_name,
                        "error_detail": error_message,
                    }
                    return HttpResponse(template.render(context, request), status=503)

        return None
