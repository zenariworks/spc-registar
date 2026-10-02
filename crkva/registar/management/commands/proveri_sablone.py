"""Audit Django templates for attribute chains that the model schema cannot resolve.

Templates render `{{ obj.foo.bar }}` to the empty string when `.bar` does not
exist on `foo`. This command walks every template in `crkva/registar/templates/`,
extracts every dotted variable chain, infers the type of the root variable from
a small heuristic table (plus `{% for X in Y %}` loop inference), and reports
chains that cannot be resolved against the Django model schema.

Two severities are emitted:

* ``HARD``  -- chain whose root resolves to a known model and at least one step
  of the dotted access is provably wrong (e.g. attribute access on a
  ``CharField``, missing model attribute/property, wrong related name).
* ``SOFT``  -- chain rooted at a known model but the audit cannot finish walking
  it (e.g. crossed a custom property whose return type is unknown). Reported as
  context only; intentionally noisy.

The command is intentionally approximate: false positives are preferred over
false negatives. The goal is a triage list, not a rejection gate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from django.apps import apps
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from django.db.models.fields.reverse_related import ForeignObjectRel

ROOT_TO_MODEL: dict[str, str] = {
    "krstenje": "Krstenje",
    "vencanje": "Vencanje",
    "parohijan": "Osoba",
    "osoba": "Osoba",
    "domacin": "Osoba",
    "domacinstvo": "Domacinstvo",
    "svestenik": "Svestenik",
    "adresa": "Adresa",
    "slava": "Slava",
    "hram": "Hram",
    "ukucanin": "Ukucanin",
    "dete": "Osoba",
    "otac": "Osoba",
    "majka": "Osoba",
    "kum": "Osoba",
    "zenik": "Osoba",
    "nevesta": "Osoba",
    "svekar": "Osoba",
    "svekrva": "Osoba",
    "tast": "Osoba",
    "tasta": "Osoba",
    "stari_svat": "Osoba",
}
"""Root-variable heuristic table: template variable name → ``registar`` model.

Loop variables introduced via ``{% for X in Y %}`` are added dynamically; this
table is the fallback for context variables coming from views. ``entry`` and
``change`` in ``_history_panel.html`` are HistoryEntry / FieldChange
dataclasses (see ``registar/istorija.py``), not Django models, so they are
deliberately left out -- the audit can't introspect dataclass fields and would
flag every access.
"""

COLLECTION_TO_MODEL: dict[str, str] = {
    "domacinstva": "Domacinstvo",
    "krstenja": "Krstenje",
    "vencanja": "Vencanje",
    "svestenici": "Svestenik",
    "parohijani": "Osoba",
    "osobe": "Osoba",
    "slave": "Slava",
    "hramovi": "Hram",
    "ukucani": "Ukucanin",
}
"""Loop collection name → element model, to type ``X`` in ``{% for X in Y %}``."""

QUERYSET_TERMINALS = {"all", "count", "first", "last", "exists", "filter", "exclude"}
"""QuerySet / Manager attributes that end the walk without running queries."""

TEMPLATE_BUILTINS = {
    "pk",
    "id",
    "uid",
    "get_absolute_url",
    "DoesNotExist",
    "MultipleObjectsReturned",
}
"""Pseudo-attributes every model effectively has; the walk stops on them."""

TEMPLATE_FILTER_TOKENS = {
    "default",
    "default_if_none",
    "yesno",
    "length",
    "length_is",
    "date",
    "time",
    "lower",
    "upper",
    "safe",
    "escape",
    "truncatechars",
    "truncatewords",
    "join",
    "first",
    "last",
    "stringformat",
    "floatformat",
}
"""Filter / tag fragments that must not be mistaken for attribute access."""

SKIP_ROOTS = {
    "request",
    "form",
    "view",
    "block",
    "user",
    "perms",
    "messages",
    "csrf_token",
    "is_paginated",
    "page_obj",
    "paginator",
    "object_list",
    "object",
    "field",
    "forloop",
    "STATIC_URL",
    "MEDIA_URL",
    "LANGUAGE_CODE",
    "True",
    "False",
    "None",
}
"""Roots that are not model context: ``request.user.x``, ``form.x``, ``view.x`` …"""

DATETIME_ATTRS = {"year", "month", "day", "hour", "minute", "second"}
"""Attributes allowed on date/time fields."""

VIEW_ANNOTATED_QUERYSETS = {"zivi_clanovi", "preminuli_clanovi"}
"""Lists the views attach to Domacinstvo in a loop (domacinstvo_view, slava_view).

They are not ``Prefetch(to_attr=...)`` attributes, so they lack the
``prefetched_`` prefix, and templates guard them with ``{% if %}``.
"""

TOKEN_RE = re.compile(r"\{[%{]\s*(.+?)\s*[%}]\}", re.DOTALL)
"""A ``{{ ... }}`` or ``{% ... %}`` construct; group 1 is its body."""

FOR_RE = re.compile(r"for\s+([\w,\s]+?)\s+in\s+([\w\.]+)")

CHAIN_RE = re.compile(r"\b([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)+)\b")
"""A dotted chain ``foo.bar(.baz)*``; bare ``foo`` is skipped since it can't fail silently."""


@dataclass
class Finding:
    """One reported chain; ``severity`` is ``"HARD"`` or ``"SOFT"``."""

    file: str
    line: int
    chain: str
    severity: str
    reason: str

    def format(self) -> str:
        return (
            f"{self.severity}  {self.file}:{self.line}  {self.chain}  -- {self.reason}"
        )


def iter_chains_with_lines(text: str) -> Iterable[tuple[int, str, dict[str, str]]]:
    """Yield ``(line, chain, loop_vars_so_far)`` for every dotted chain.

    Tags and variables are processed in document order, so ``{% for X in Y %}``
    bindings are seen before chains that use them. ``loop_vars_so_far``
    accumulates those bindings. This is approximate: ``{% endfor %}`` is not
    tracked, so loops that share a variable name across the file settle on the
    most recent binding. For an audit that's fine.

    Tag bodies are scanned whole (``{% if foo.bar %}``,
    ``{% url 'x' uid=obj.adresa.ulica %}``); variable bodies lose their filters
    first.
    """
    loop_vars: dict[str, str] = {}
    for m in TOKEN_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        body = m.group(1)
        if text.startswith("{%", m.start()):
            _bind_loop_vars(body, loop_vars)
        else:
            body = strip_filters(body)
        for chain_match in CHAIN_RE.finditer(body):
            yield line, chain_match.group(1), dict(loop_vars)


def _bind_loop_vars(tag_body: str, loop_vars: dict[str, str]) -> None:
    """Types the names of a ``{% for %}`` tag.

    The collection table wins; otherwise a loop variable that is itself a known
    root name (``for ukucanin in domacinstvo.ukucani.all``) keeps that type.
    Anything else stays untyped.
    """
    for_match = FOR_RE.search(tag_body)
    if not for_match:
        return
    names = [n.strip() for n in for_match.group(1).split(",") if n.strip()]
    model_name = COLLECTION_TO_MODEL.get(for_match.group(2).split(".")[0])
    for n in names:
        tip = model_name or ROOT_TO_MODEL.get(n)
        if tip:
            loop_vars[n] = tip


def strip_filters(expr: str) -> str:
    """Drop filter pipes from a variable expression body.

    ``foo.bar|default:"x"|length`` becomes ``foo.bar``. Filter names and their
    arguments are not attribute chains; ignoring them avoids false positives.
    """
    return expr.split("|", 1)[0]


def resolve_model(name: str) -> type[Model] | None:
    """Look up a model class by short name in the ``registar`` app."""
    try:
        return apps.get_model("registar", name)
    except LookupError:
        return None


def step(model: type[Model], attr: str) -> tuple[str, object]:
    """Take one step along a dotted chain.

    Returns ``(kind, target)`` where ``kind`` is one of:

    * ``"model"`` -- resolved to another model class; ``target`` is the class
    * ``"scalar"`` -- resolved to a non-relational field; ``target`` is the
      field instance
    * ``"queryset"`` -- resolved to a reverse FK / M2M manager; ``target`` is
      the model class of the queryset element
    * ``"property"`` -- resolved to a property/method we cannot introspect;
      ``target`` is ``None``
    * ``"missing"`` -- attribute does not exist on the model

    Attributes added at runtime via ``Prefetch(to_attr="prefetched_xxx")`` are
    invisible to ``_meta.get_field`` and ``dir(cls)``; by convention they are
    all named ``prefetched_*`` and treated as opaque querysets, like the
    view-annotated lists. The caller decides severity.
    """
    if attr in TEMPLATE_BUILTINS:
        return "scalar", None
    if attr.startswith("prefetched_") or attr in VIEW_ANNOTATED_QUERYSETS:
        return "queryset", None
    try:
        field = model._meta.get_field(attr)
    except FieldDoesNotExist:
        if getattr(model, attr, None) is None:
            return "missing", None
        return "property", None
    return _field_kind(field)


def _field_kind(field) -> tuple[str, object]:
    """``step`` result for a Django field; reverse one-to-one is a model."""
    if isinstance(field, (ForeignKey, OneToOneField)):
        return "model", field.related_model
    if isinstance(field, ManyToManyField):
        return "queryset", field.related_model
    if isinstance(field, ForeignObjectRel):
        return ("model" if field.one_to_one else "queryset"), field.related_model
    return "scalar", field


def walk(model: type[Model], parts: list[str]) -> tuple[str, str] | None:
    """Walk a chain rooted at ``model``.

    Returns ``None`` if everything resolves cleanly. Otherwise returns
    ``(severity, reason)``.
    """
    kind: str = "model"
    target: object = model
    for i, attr in enumerate(parts):
        if kind != "model":
            return _step_past_model(kind, target, attr, ".".join(parts[:i]))
        next_kind, next_target = step(target, attr)
        if next_kind == "missing":
            return "HARD", f"step '{attr}' not found on {target.__name__}"
        kind, target = next_kind, next_target
    return None


def _step_past_model(
    kind: str, target: object, attr: str, parent: str
) -> tuple[str, str] | None:
    """Judge ``.attr`` on something that is not a model.

    * scalar -- the classic bug (``CharField.naziv``) is HARD; a few datetime
      attributes are allowed.
    * queryset -- terminals (``.all``) and numeric list indexes
      (``prefetched_ukucanstva.0``) end the walk; anything else needs a query
      to judge, so SOFT.
    * property/method -- unknown return type, so SOFT.
    """
    if kind == "scalar":
        if attr in DATETIME_ATTRS:
            return None
        ftype = type(target).__name__ if target is not None else "scalar"
        return (
            "HARD",
            f"step '{attr}' accesses attribute on {ftype} (parent: {parent})",
        )
    if kind == "queryset":
        if attr in QUERYSET_TERMINALS or attr.isdigit():
            return None
        return "SOFT", f"step '{attr}' on queryset (parent: {parent})"
    return "SOFT", f"step '{attr}' after property/method (parent: {parent})"


def _root_model(chain: str, loop_vars: dict[str, str]) -> type[Model] | None:
    """Model of the chain's root variable, or None if the root is not audited."""
    root = chain.split(".")[0]
    if root in SKIP_ROOTS or root in TEMPLATE_FILTER_TOKENS:
        return None
    model_name = loop_vars.get(root) or ROOT_TO_MODEL.get(root)
    if not model_name:
        return None
    return resolve_model(model_name)


def audit_template(text: str, file: str, severity: str) -> tuple[list[Finding], int]:
    """Findings for one template (filtered by ``severity``) and chains checked."""
    findings: list[Finding] = []
    checked = 0
    for line, chain, loop_vars in iter_chains_with_lines(text):
        model = _root_model(chain, loop_vars)
        if model is None:
            continue
        checked += 1
        result = walk(model, chain.split(".")[1:])
        if result is not None and severity in ("ALL", result[0]):
            findings.append(Finding(file, line, chain, *result))
    return findings, checked


class Command(BaseCommand):
    help = "Audit registar templates for unresolvable attribute chains."

    def add_arguments(self, parser):
        parser.add_argument(
            "--templates-dir",
            default=None,
            help="Override templates root (defaults to crkva/registar/templates).",
        )
        parser.add_argument(
            "--severity",
            choices=["HARD", "SOFT", "ALL"],
            default="ALL",
            help="Filter findings by severity (default ALL).",
        )

    def handle(self, *args, **opts):
        templates_dir = opts["templates_dir"]
        if templates_dir is None:
            templates_dir = Path(settings.BASE_DIR) / "registar" / "templates"
        templates_dir = Path(templates_dir)

        if not templates_dir.exists():
            self.stderr.write(f"Templates dir not found: {templates_dir}")
            return

        findings: list[Finding] = []
        chains_checked = 0
        for html in sorted(templates_dir.rglob("*.html")):
            found, checked = audit_template(
                html.read_text(encoding="utf-8"),
                str(html.relative_to(templates_dir.parent)),
                opts["severity"],
            )
            findings += found
            chains_checked += checked
        self._report(findings, chains_checked)

    def _report(self, findings: list[Finding], chains_checked: int) -> None:
        """Counts first, then HARD findings, then SOFT ones."""
        hard = [f for f in findings if f.severity == "HARD"]
        soft = [f for f in findings if f.severity == "SOFT"]

        self.stdout.write(f"# chains checked: {chains_checked}")
        self.stdout.write(f"# HARD findings: {len(hard)}")
        self.stdout.write(f"# SOFT findings: {len(soft)}")
        self.stdout.write("")

        for f in hard:
            self.stdout.write(f.format())
        if hard and soft:
            self.stdout.write("")
        for f in soft:
            self.stdout.write(f.format())
