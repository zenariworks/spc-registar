from django.urls import include, path

from . import views

handler404 = "registar.views.custom_404"
urlpatterns = [
    path("slava/<uuid:uid>/", views.prikazi_domacinstva, name="prikazi_domacinstva"),
    path("", views.index, name="pocetna"),
    path("select2/", include("django_select2.urls")),
    path("parohijani/", views.SpisakParohijana.as_view(), name="parohijani"),
    path(
        "parohijan/<uuid:uid>/",
        views.PrikazParohijana.as_view(),
        name="parohijan_detail",
    ),
    path(
        "parohijan/print/<uuid:uid>/",
        views.ParohijanPDF.as_view(),
        name="parohijan_pdf",
    ),
    path("krstenja/", views.SpisakKrstenja.as_view(), name="krstenja"),
    path(
        "krstenje/<uuid:uid>/", views.PrikazKrstenja.as_view(), name="krstenje_detail"
    ),
    path(
        "krstenje/print/<uuid:uid>/", views.KrstenjePDF.as_view(), name="krstenje_pdf"
    ),
    path("vencanja/", views.SpisakVencanja.as_view(), name="vencanja"),
    path(
        "vencanje/<uuid:uid>/", views.PrikazVencanja.as_view(), name="vencanje_detail"
    ),
    path(
        "vencanje/print/<uuid:uid>/", views.VencanjePDF.as_view(), name="vencanje_pdf"
    ),
    path("svestenici/", views.SpisakSvestenika.as_view(), name="svestenici"),
    path(
        "svestenik/<uuid:uid>/",
        views.PrikazSvestenika.as_view(),
        name="svestenik_detail",
    ),
    path(
        "svestenik/print/<uuid:uid>/",
        views.SvestenikPDF.as_view(),
        name="svestenik_pdf",
    ),
    path(
        "veroisposvest/dodaj/",
        views.dodaj_izmeni_veroispovest,
        name="dodaj-veroisposvest",
    ),
    path(
        "veroisposvest/izmeni/<uuid:uid>/",
        views.dodaj_izmeni_veroispovest,
        name="izmeni-veroisposvest",
    ),
    path("search/", views.search_view, name="search_view"),
    path("unos/parohijan/", views.unos_parohijana, name="unos_parohijana"),
    path("unos/krstenje/", views.unos_krstenja, name="unos_krstenja"),
]
