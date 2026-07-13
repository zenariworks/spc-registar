"""Заједничке базе за ``unos_*``/``izmena_*`` токове регистра (issue #363).

Десет FBV приказа делило је исти костур (POST → валидација → сачувај →
redirect, иначе форма → render). Овде је извучен у ``CreateView``/
``UpdateView`` поткласе. ``tenant_role_required`` се примењује као
dispatch mixin (обухвата и ``login_required``, па се понаша идентично
као стари декоратор), а специфичности (``parohijan=True``, Ukucanin
формсет, „Измена" chrome) остају у поткласама.
"""

from __future__ import annotations

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, UpdateView
from tenants.permissions import tenant_role_required


class TenantRoleMixin:
    """Гејтуј приказ кроз ``tenant_role_required(role)`` на dispatch-у.

    Поткласа поставља ``role`` (нпр. ``"krstenje"``).
    """

    role: str = ""

    def dispatch(self, request, *args, **kwargs):
        guard = tenant_role_required(self.role)
        return guard(super().dispatch)(request, *args, **kwargs)


class RegistarCreateView(TenantRoleMixin, CreateView):
    """Унос нове инстанце: празна форма, па POST → сачувај → списак.

    Поткласа поставља ``form_class``, ``template_name``,
    ``context_object_name``, ``role`` и ``success_url_name`` (рут списка).
    """

    success_url_name: str = ""

    def get_success_url(self) -> str:
        return reverse(self.success_url_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        context.setdefault(self.context_object_name, None)
        return context


class RegistarUpdateView(TenantRoleMixin, UpdateView):
    """Измена постојеће инстанце тражене по ``uid``.

    Поткласа поставља ``model``/``form_class``, ``template_name``,
    ``context_object_name``, ``role`` и ``detail_url_name`` (рут детаља).
    """

    slug_field = "uid"
    slug_url_kwarg = "uid"
    detail_url_name: str = ""

    def get_success_url(self) -> str:
        return reverse(self.detail_url_name, kwargs={"uid": self.object.uid})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        context.setdefault(self.context_object_name, self.object)
        return context


class EditChromeMixin:
    """Додаје ``title``/``back_url`` као стари FBV-ови за свештеника,
    парохијана и домаћинство (крштење/венчање их немају)."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Измена"
        context["back_url"] = reverse(
            self.detail_url_name, kwargs={"uid": self.object.uid}
        )
        return context


class ForceParohijanMixin:
    """Постави ``parohijan=True`` при чувању (унос и измена), уз
    ``commit=False`` + ``save_m2m`` — исти образац као стари FBV-ови."""

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.parohijan = True
        self.object.save()
        form.save_m2m()
        return HttpResponseRedirect(self.get_success_url())
