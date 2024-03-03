from django.shortcuts import redirect, render
from registar.forms import VeroispovestForm
from registar.models import Veroispovest

from .krstenje_view import *
from .vencanje_view import *
from .parohijan_view import *
from .svestenik_view import *
from .view_404 import *


def index(request):
    return render(request, "registar/index.html")


def dodaj_izmeni_veroispovest(request, uid=None):
    if uid:
        veroispovest = Veroispovest.objects.get(uid=uid)
        form = VeroispovestForm(request.POST or None, instance=veroispovest)
    else:
        form = VeroispovestForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect(
                "nekigde"
            )  # Редирект на другу страницу након успешног уноса

    return render(
        request=request,
        template_name="registar/form_veroispovest.html",
        context={"form": form},
    )


# In your views.py
def search_view(request) -> HttpResponse:
    query = request.GET.get("query", "")
    if query:
        results = Veroispovest.objects.filter(naziv__icontains=query)
    else:
        results = Veroispovest.objects.none()

    return render(
        request=request,
        template_name="registar/search_view.html",
        context={"results": results},
    )
