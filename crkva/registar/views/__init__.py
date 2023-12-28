from django.shortcuts import render

from .krstenje_view import *
from .svestenik_view import *
from .osoba_view import *
from .view_404 import *


def index(request):
    return render(request, "registar/index.html")
