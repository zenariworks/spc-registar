"""Tenant switching + self-edit profile views."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from tenants.forms import ProfileForm
from tenants.middleware import SESSION_TENANT_KEY
from tenants.models import Tenant, UserMembership


@login_required
@require_POST
def switch_tenant(request: HttpRequest, tenant_id: int) -> HttpResponse:
    """Set the active tenant on the session, then redirect back."""
    tenant = get_object_or_404(Tenant, pk=tenant_id, is_active=True)

    if not request.user.is_superuser:
        allowed = UserMembership.objects.filter(
            user=request.user, tenant=tenant
        ).exists()
        if not allowed:
            return HttpResponse(status=403)

    request.session[SESSION_TENANT_KEY] = tenant.pk

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    fallback_url = reverse("pocetna")
    if not next_url or not url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = fallback_url
    return HttpResponseRedirect(next_url)


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """Self-edit profile. Two forms in one page: info + password."""
    info_form = ProfileForm(instance=request.user)
    password_form = PasswordChangeForm(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "info":
            info_form = ProfileForm(request.POST, instance=request.user)
            if info_form.is_valid():
                info_form.save()
                messages.success(request, "Подаци сачувани.")
                return redirect("tenants:profile")
        elif action == "password":
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # keep the user logged in after their password changes
                update_session_auth_hash(request, user)
                messages.success(request, "Лозинка промењена.")
                return redirect("tenants:profile")

    return render(
        request,
        "registar/profile.html",
        {"info_form": info_form, "password_form": password_form},
    )
