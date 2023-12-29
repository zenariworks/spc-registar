from django.conf.urls import handler404
from django.urls import path

from . import views


handler404 = 'registar.views.custom_404'
urlpatterns = [
    path("", views.index, name="pocetna"),

    path("osobe/", views.OsobeList.as_view(), name="osobe"),
    path("osoba/<uuid:uid>/", views.OsobaView.as_view(), name="osoba_detail"),
    path("osoba/print/<uuid:uid>/", views.OsobaPDF.as_view(), name="osoba_pdf"),

    path("krstenja/", views.KrstenjeSpisak.as_view(), name="krstenja"),
    path("krstenje/<uuid:uid>/", views.KrstenjePrikaz.as_view(), name="krstenje_detail"),
    path("krstenje/print/<uuid:uid>/", views.KrstenjePDF.as_view(), name="krstenje_pdf"),

    path("svestenici/", views.SvesteniciSpisak.as_view(), name="svestenici"),
    path("svestenik/<uuid:uid>/", views.SvestenikPrikaz.as_view(), name="svestenik_detail"),
    path("svestenik/print/<uuid:uid>/", views.SvestenikPDF.as_view(), name="svestenik_pdf"),

    path('veroisposvest/dodaj/', views.dodaj_izmeni_veroispovest, name='dodaj-veroisposvest'),
    path('veroisposvest/izmeni/<uuid:uid>/', views.dodaj_izmeni_veroispovest, name='izmeni-veroisposvest'),

]
