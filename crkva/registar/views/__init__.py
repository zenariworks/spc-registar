from django.shortcuts import render

from .svestenik_view import *


def index(request):
    return render(request, 'registar/index.html')
