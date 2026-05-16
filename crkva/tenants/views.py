"""Tenant switching, self-profile, and admin user-management views."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from tenants.forms import AddUserForm, EditRoleForm, ProfileForm
from tenants.middleware import SESSION_TENANT_KEY
from tenants.models import Tenant, UserMembership
from tenants.permissions import tenant_admin_required

User = get_user_model()


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
                update_session_auth_hash(request, user)
                messages.success(request, "Лозинка промењена.")
                return redirect("tenants:profile")

    return render(
        request,
        "registar/profile.html",
        {"info_form": info_form, "password_form": password_form},
    )


@tenant_admin_required
def user_list(request: HttpRequest) -> HttpResponse:
    """List memberships for the active tenant."""
    memberships = (
        UserMembership.objects.filter(tenant=request.tenant)
        .select_related("user")
        .order_by("user__username")
    )
    return render(
        request,
        "registar/users_list.html",
        {"memberships": memberships},
    )


@tenant_admin_required
def user_add(request: HttpRequest) -> HttpResponse:
    """Create a new User + UserMembership scoped to the active tenant."""
    form = AddUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
        )
        UserMembership.objects.create(
            user=user,
            tenant=request.tenant,
            role=data["role"],
            is_default=data["is_default"],
        )
        messages.success(request, f"Корисник {user.username} креиран.")
        return redirect("tenants:user_list")
    return render(request, "registar/users_add.html", {"form": form})


@tenant_admin_required
@require_POST
def user_edit_role(request: HttpRequest, user_id: int) -> HttpResponse:
    """Change a membership's role inside the active tenant."""
    membership = get_object_or_404(
        UserMembership, user_id=user_id, tenant=request.tenant
    )
    form = EditRoleForm(request.POST)
    if form.is_valid():
        membership.role = form.cleaned_data["role"]
        membership.save(update_fields=["role"])
        messages.success(request, f"Улога ажурирана за {membership.user.username}.")
    return redirect("tenants:user_list")


@tenant_admin_required
@require_POST
def user_deactivate(request: HttpRequest, user_id: int) -> HttpResponse:
    """Toggle User.is_active for a member of the active tenant."""
    membership = get_object_or_404(
        UserMembership, user_id=user_id, tenant=request.tenant
    )
    target = membership.user
    if target.pk == request.user.pk:
        messages.error(request, "Не можете деактивирати свој налог.")
        return redirect("tenants:user_list")
    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])
    verb = "активиран" if target.is_active else "деактивиран"
    messages.success(request, f"Корисник {target.username} {verb}.")
    return redirect("tenants:user_list")
