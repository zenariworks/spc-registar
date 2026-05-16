"""URL patterns for the tenants app."""

from django.urls import path
from tenants import views

app_name = "tenants"

urlpatterns = [
    path("switch/<int:tenant_id>/", views.switch_tenant, name="switch"),
    path("profile/", views.profile, name="profile"),
]
