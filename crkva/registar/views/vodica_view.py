"""Васкршња водица — обједињена са славском страницом Васкрса (#325).

Раније је постојао засебан извештај по улицама, али је дуплирао приказ славе
Васкрса (домаћинства са `vaskrsnja_vodica=True`). Сада је то једна страница:
ова рута само преусмерава на `slava_detail` за Васкрс, чувајући избор свештеника
(`?svestenik=`), тако да и сајдбар и календар воде на исти приказ.
"""

from __future__ import annotations

from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from kalendar.models import Slava


@login_required
def vaskrsnja_vodica(request: HttpRequest) -> HttpResponse:
    """Преусмерава на обједињену страницу васкршње водице (слава Васкрса)."""
    vaskrs = Slava.get_vaskrs()
    if vaskrs is None:
        # Васкрс није дефинисан у календару — нема циљ за преусмерење.
        return redirect("kalendar")
    url = reverse("slava_detail", kwargs={"uid": vaskrs.uid})

    # Очувај само очекивани параметар, уместо целог корисничког query string-а.
    svestenik = request.GET.get("svestenik")
    query = urlencode({"svestenik": svestenik}) if svestenik else ""

    return redirect(f"{url}?{query}" if query else url)
