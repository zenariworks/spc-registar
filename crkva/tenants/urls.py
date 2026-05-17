"""URL patterns for the tenants app."""

from django.urls import path
from tenants import views

app_name = "parohija"

urlpatterns = [
    path("switch/<int:tenant_id>/", views.switch_tenant, name="switch"),
    path("profile/", views.profile, name="profile"),
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_add, name="user_add"),
    path("users/<int:user_id>/role/", views.user_edit_role, name="user_edit_role"),
    path(
        "users/<int:user_id>/deactivate/",
        views.user_deactivate,
        name="user_deactivate",
    ),
]
