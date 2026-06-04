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
                return redirect("parohija:profile")
        elif action == "password":
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Лозинка промењена.")
                return redirect("parohija:profile")

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
        "registar/spisak_korisnika.html",
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
        return redirect("parohija:user_list")
    return render(request, "registar/unos_korisnika.html", {"form": form})


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
    return redirect("parohija:user_list")


@tenant_admin_required
@require_POST
def user_deactivate(request: HttpRequest, user_id: int) -> HttpResponse:
    """Toggle membership.is_active for a member of the active tenant.

    Scoped to request.tenant: this locks the user out of *this* parish only.
    It never touches the shared User.is_active flag, so a user who belongs to
    several parishes keeps access to the others (issue #227).
    """
    membership = get_object_or_404(
        UserMembership, user_id=user_id, tenant=request.tenant
    )
    if membership.user_id == request.user.pk:
        messages.error(request, "Не можете деактивирати свој налог.")
        return redirect("parohija:user_list")
    membership.is_active = not membership.is_active
    membership.save(update_fields=["is_active"])
    verb = "активиран" if membership.is_active else "деактивиран"
    messages.success(request, f"Корисник {membership.user.username} {verb}.")
    return redirect("parohija:user_list")
