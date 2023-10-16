from django.shortcuts import render

from .krstenje_view import *
from .svestenik_view import *


def index(request):
    return render(request, "registar/index.html")
