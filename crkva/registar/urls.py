from django.urls import path

from . import views
from .views import SvestenikView, SvestenikPDF
from .views import KrstenjeView, KrstenjePDF, KrstenjaListView
from .views import OsobaView, OsobeListView, OsobaPDF


urlpatterns = [
    path("", views.index, name="index"),

    path("osobe/", OsobeListView.as_view(), name="osobe"),
    path("osoba/<uuid:uid>/", OsobaView.as_view(), name="osoba_detail"),
    path("osoba/print/<uuid:uid>/", OsobaPDF.as_view(), name="osoba_pdf"),


    path('krstenja/', KrstenjaListView.as_view(), name='krstenja'),
    path("krstenje/<uuid:uid>/", KrstenjeView.as_view(), name="krstenje_detail"),
    path("krstenje/print/<uuid:uid>/", KrstenjePDF.as_view(), name="krstenje_pdf"),

    path("svestenik/<uuid:uid>/", SvestenikView.as_view(), name="svestenik_detail"),
    path("svestenik/print/<uuid:uid>/", SvestenikPDF.as_view(), name="svestenik_pdf"),
]
