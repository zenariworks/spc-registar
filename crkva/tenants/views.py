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
        # Мора да се поклапа са провером у middleware-у (_membership тражи
        # is_active=True); иначе деактивиран члан „пребаци" парохију коју
        # middleware потом одбије (#340).
        allowed = UserMembership.objects.filter(
            user=request.user, tenant=tenant, is_active=True
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
    """List memberships for the active tenant, with priest links (#278)."""
    from registar.models import Svestenik

    memberships = list(
        UserMembership.objects.filter(tenant=request.tenant)
        .select_related("user")
        .order_by("user__username")
    )
    svestenici = list(
        Svestenik.objects.select_related("parohija").order_by("prezime", "ime")
    )
    sv_by_user = {s.user_id: s for s in svestenici if s.user_id}
    for membership in memberships:
        membership.svestenik = sv_by_user.get(membership.user_id)
    return render(
        request,
        "registar/spisak_korisnika.html",
        {"memberships": memberships, "svestenici": svestenici},
    )


@tenant_admin_required
def user_add(request: HttpRequest) -> HttpResponse:
    """Create a new User + UserMembership scoped to the active tenant."""
    form = AddUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        # Постојеће корисничко име → вежи постојећег корисника за ову парохију;
        # ново → направи налог. Постојећем НЕ дирамо лозинку/профил (admin једне
        # парохије не сме да ресетује глобални налог). (#228)
        user = User.objects.filter(username=data["username"]).first()
        is_new = user is None
        if is_new:
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
            )
        if UserMembership.objects.filter(user=user, tenant=request.tenant).exists():
            form.add_error(None, f"Корисник {user.username} је већ члан ове парохије.")
        else:
            if data["is_default"]:
                # Тачно једна подразумевана парохија по кориснику.
                UserMembership.objects.filter(user=user, is_default=True).update(
                    is_default=False
                )
            UserMembership.objects.create(
                user=user,
                tenant=request.tenant,
                role=data["role"],
                is_default=data["is_default"],
            )
            if is_new:
                messages.success(request, f"Корисник {user.username} креиран.")
            else:
                messages.success(
                    request,
                    f"Постојећи корисник {user.username} додат у ову парохију.",
                )
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
def user_bind_svestenik(request: HttpRequest, user_id: int) -> HttpResponse:
    """Bind (or clear) the Svestenik profile linked to a user's login (#278).

    The footer signature on certificates uses the logged-in user's linked
    Svestenik; this is where an admin sets that link. ``Svestenik.user`` is
    one-to-one per schema, so any prior link for this user is cleared first.
    """
    from registar.models import Svestenik

    membership = get_object_or_404(
        UserMembership, user_id=user_id, tenant=request.tenant
    )
    user = membership.user
    sv_id = (request.POST.get("svestenik") or "").strip()

    chosen = None
    if sv_id:
        chosen = get_object_or_404(Svestenik, pk=sv_id)
        if chosen.user_id and chosen.user_id != user.pk:
            messages.error(
                request,
                f"Свештеник {chosen} је већ везан за корисника "
                f"{chosen.user.username}.",
            )
            return redirect("parohija:user_list")

    # OneToOne per schema: a user maps to one priest — clear any prior link.
    Svestenik.objects.filter(user=user).update(user=None)
    if chosen is not None:
        chosen.user = user
        chosen.save(update_fields=["user"])
        messages.success(request, f"{user.username} → {chosen}.")
    else:
        messages.success(request, f"Веза са свештеником уклоњена за {user.username}.")
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
