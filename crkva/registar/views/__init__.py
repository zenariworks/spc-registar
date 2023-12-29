from django.shortcuts import render, redirect

from registar.forms import VeroispovestForm

from .krstenje_view import *
from .svestenik_view import *
from .osoba_view import *
from .view_404 import *

from registar.models import Veroispovest


def index(request):
    return render(request, "registar/index.html")

def dodaj_izmeni_veroispovest(request, uid=None):
    if uid:
        veroispovest = Veroispovest.objects.get(uid=uid)
        form = VeroispovestForm(request.POST or None, instance=veroispovest)
    else:
        form = VeroispovestForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('nekigde')  # Редирект на другу страницу након успешног уноса

    return render(request, 'registar/form_veroispovest.html', {'form': form})

# In your views.py
def search_view(request):
    query = request.GET.get('query', '')
    # Implement your search logic here
    # ...
    return render(request, 'registar/search_results.html', context)
