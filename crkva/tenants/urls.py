"""URL patterns for the tenants app."""

from django.urls import path
from tenants import views

app_name = "parohija"

urlpatterns = [
    path("promena/<int:parohija_id>/", views.promena_parohije, name="promena"),
    path("profil/", views.profil, name="profil"),
    path("korisnici/", views.korisnici, name="korisnici"),
    path("korisnici/add/", views.dodavanje, name="dodavanje"),
    path("korisnici/<int:user_id>/role/", views.izmena_uloge, name="izmena_uloge"),
    path(
        "korisnici/<int:user_id>/svestenik/",
        views.user_bind_svestenik,
        name="user_bind_svestenik",
    ),
    path(
        "korisnici/<int:user_id>/deactivate/",
        views.deaktiviranje,
        name="deaktiviranje",
    ),
]
