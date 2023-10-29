from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="pocetna"),

    path("osobe/", views.OsobeList.as_view(), name="osobe"),
    path("osoba/<uuid:uid>/", views.OsobaView.as_view(), name="osoba_detail"),
    path("osoba/print/<uuid:uid>/", views.OsobaPDF.as_view(), name="osoba_pdf"),

    path('krstenja/', views.KrstenjaList.as_view(), name='krstenja'),
    path("krstenje/<uuid:uid>/", views.KrstenjeView.as_view(), name="krstenje_detail"),
    path("krstenje/print/<uuid:uid>/", views.KrstenjePDF.as_view(), name="krstenje_pdf"),

    path("svestenici/", views.SvesteniciList.as_view(), name="svestenici"),
    path("svestenik/<uuid:uid>/", views.SvestenikView.as_view(), name="svestenik_detail"),
    path("svestenik/print/<uuid:uid>/", views.SvestenikPDF.as_view(), name="svestenik_pdf"),
]
