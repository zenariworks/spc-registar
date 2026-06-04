"""Овај модул дефинише URL обрасце за апликацију регистар."""

from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

handler404 = "registar.views.custom_404"
urlpatterns = [
    path(
        "prijava/",
        auth_views.LoginView.as_view(template_name="registar/login.html"),
        name="login",
    ),
    path("odjava/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("", views.index, name="pocetna"),
    path("select2/", include("django_select2.urls")),
    path("slava-kalendar/", views.kalendar, name="kalendar"),
    path(
        "slava-kalendar/<int:year>/<int:month>/",
        views.kalendar,
        name="kalendar_mesec",
    ),
    path("slava/<int:uid>/", views.slava_domacinstva, name="slava_detail"),
    path(
        "izvestaj/vaskrsnja-vodica/",
        views.vaskrsnja_vodica,
        name="vaskrsnja_vodica",
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
    path("domacinstva/", views.SpisakDomacinsta.as_view(), name="domacinstva"),
    path(
        "domacinstva/print/",
        views.domacinstva_print,
        name="domacinstva_print",
    ),
    path(
        "domacinstvo/<uuid:uid>/",
        views.PrikazDomacinstva.as_view(),
        name="domacinstvo_detail",
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
    path("vencanje/calibrate/", views.calibrate_vencanje, name="calibrate_vencanje"),
    path("krstenje/calibrate/", views.calibrate_krstenje, name="calibrate_krstenje"),
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
    path("api/search/", views.search_autocomplete, name="search_autocomplete"),
    path("api/brzi-unos-osobe/", views.brzi_unos_osobe, name="brzi_unos_osobe"),
    path("api/brzi-unos-adrese/", views.brzi_unos_adrese, name="brzi_unos_adrese"),
    path("api/brzi-unos-hrama/", views.brzi_unos_hrama, name="brzi_unos_hrama"),
    path(
        "api/brzi-izmena-adrese/<uuid:uid>/",
        views.brzi_izmena_adrese,
        name="brzi_izmena_adrese",
    ),
    path("unos/parohijan/", views.unos_parohijana, name="unos_parohijana"),
    path("unos/krstenje/", views.unos_krstenja, name="unos_krstenja"),
    path("unos/vencanje/", views.unos_vencanja, name="unos_vencanja"),
    path("unos/svestenik/", views.unos_svestenika, name="unos_svestenika"),
    path("unos/domacinstvo/", views.unos_domacinstva, name="unos_domacinstva"),
    path(
        "izmena/parohijan/<int:uid>/", views.izmena_parohijana, name="izmena_parohijana"
    ),
    path("izmena/krstenje/<uuid:uid>/", views.izmena_krstenja, name="izmena_krstenja"),
    path("izmena/vencanje/<uuid:uid>/", views.izmena_vencanja, name="izmena_vencanja"),
    path(
        "izmena/svestenik/<int:uid>/", views.izmena_svestenika, name="izmena_svestenika"
    ),
    path(
        "izmena/domacinstvo/<uuid:uid>/",
        views.izmena_domacinstva,
        name="izmena_domacinstva",
    ),
    path("adrese/duplikati/", views.duplikati_adresa, name="duplikati_adresa"),
    path(
        "adresa/<uuid:loser_uid>/spoji/<uuid:winner_uid>/",
        views.spoji_adresu,
        name="spoji_adresu",
    ),
]
