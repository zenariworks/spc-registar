"""Заједничка база за PDF приказе (WeasyPrint).

Изводи шаблон приказа у PDF. Уклања дуплирани
``get_object``/``render_to_response``/``get`` који је постојао у приказима
крштења, венчања, свештеника и парохијана. Сваки приказ дефинише само
``model``, ``template_name``, ``filename_prefix`` и опционо ``related``
(за ``select_related``) и ``snapshot_roles`` (за историјске снимке особа).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView
from weasyprint import HTML


class HistorySnapshotMixin:
    """Додаје ревизиону историју и историјске снимке особа у контекст.

    Увек додаје ``history_entries`` (ревизије самог објекта). Ако приказ
    дефинише ``snapshot_roles``, за сваку улогу додаје ``<role>_snapshot`` —
    снимак везане особе на дан догађаја (``datum``, иначе ``created``).
    """

    snapshot_roles: list[str] = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from registar.history import history_for

        obj = self.object
        context["history_entries"] = history_for(obj)
        if self.snapshot_roles:
            event_date = getattr(obj, "datum", None) or obj.created
            for role in self.snapshot_roles:
                osoba = getattr(obj, role)
                if osoba is None:
                    context[f"{role}_snapshot"] = None
                    continue
                try:
                    context[f"{role}_snapshot"] = osoba.history.as_of(event_date)
                except type(osoba).DoesNotExist:
                    context[f"{role}_snapshot"] = osoba
        return context


class PdfDetailView(LoginRequiredMixin, DetailView):
    """База за приказе који рендерују шаблон у PDF преко WeasyPrint-а.

    Сваки приказ дефинише ``model``, ``template_name`` и ``filename_prefix``;
    опционо ``related`` за ``select_related`` при учитавању по ``uid``-у.
    """

    related: tuple[str, ...] = ()
    filename_prefix = "dokument"

    def get_object(self, queryset=None):
        base = self.model.objects
        qs = base.select_related(*self.related) if self.related else base.all()
        return get_object_or_404(qs, uid=self.kwargs.get("uid"))

    def render_to_response(self, context, **response_kwargs):
        html = render(self.request, self.template_name, context).content.decode()
        pdf = HTML(string=html, base_url=self.request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f"inline; filename={self.filename_prefix}-{self.kwargs.get('uid')}.pdf"
        )
        return response

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()  # pylint: disable=attribute-defined-outside-init
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
