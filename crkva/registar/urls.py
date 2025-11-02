"""Овај модул дефинише URL обрасце за апликацију регистар."""

from django.urls import include, path

from . import views

handler404 = "registar.views.custom_404"
urlpatterns = [
    path("", views.index, name="pocetna"),
    path("select2/", include("django_select2.urls")),
    path("slava-kalendar/", views.slava_kalendar, name="slava_kalendar"),
    path(
        "slava-kalendar/<int:year>/<int:month>/",
        views.slava_kalendar,
        name="slava_kalendar_mesec",
    ),
    path("parohijani/", views.SpisakParohijana.as_view(), name="parohijani"),
    path(
        "parohijan/<int:uid>/",
        views.PrikazParohijana.as_view(),
        name="parohijan_detail",
    ),
    path(
        "parohijan/print/<int:uid>/",
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
        "svestenik/<int:uid>/",
        views.PrikazSvestenika.as_view(),
        name="svestenik_detail",
    ),
    path(
        "svestenik/print/<int:uid>/",
        views.SvestenikPDF.as_view(),
        name="svestenik_pdf",
    ),
    path("search/", views.search_view, name="search_view"),
    path("unos/parohijan/", views.unos_parohijana, name="unos_parohijana"),
    path("unos/krstenje/", views.unos_krstenja, name="unos_krstenja"),
    path("unos/vencanje/", views.unos_vencanja, name="unos_vencanja"),
]
