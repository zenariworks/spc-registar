"""
Модул за прилагођене обрађиваче грешака.
"""

from django.shortcuts import render


def custom_404(request, exception):
    """
    Обрађује 404 грешке (страница није пронађена).

    Приказује прилагођену HTML страницу за грешку 404.
    
    :param request: Објекат HTTP захтева.
    :param exception: Изузетак повезан са 404 грешком.
    :return: HTTP одговор са статусом 404 и прилагођеним шаблоном.
    """
    return render(request, "404.html", {}, status=404)
