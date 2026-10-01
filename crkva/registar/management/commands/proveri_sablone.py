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
from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from django.db.models.fields.reverse_related import ForeignObjectRel

# ---------------------------------------------------------------------------
# Root-variable heuristic table.
#
# Maps a template variable name (the first component of a dotted chain) to a
# model name in the ``registar`` app. Loop variables introduced via
# ``{% for X in Y %}`` are added dynamically; this table is the fallback for
# context variables coming from views.
# ---------------------------------------------------------------------------
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
    # ``entry`` and ``change`` in _history_panel.html are HistoryEntry /
    # FieldChange dataclasses (see registar/istorija.py), not Django models,
    # so we deliberately leave them out of the table -- the audit can't
    # introspect dataclass fields and would flag every access.
}

# Loop collection names → element model name. Used to type ``X`` in
# ``{% for X in Y %}`` when ``Y`` is a known collection.
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

# Attributes that Django provides on every QuerySet / Manager / related
# descriptor. Walking the chain stops here -- they don't have to exist as
# fields, but we cannot introspect deeper without running queries.
QUERYSET_TERMINALS = {"all", "count", "first", "last", "exists", "filter", "exclude"}

# Template-built-in pseudo-attributes that any object effectively has access
# to. Stop walking when seen.
TEMPLATE_BUILTINS = {
    "pk",
    "id",
    "uid",
    "get_absolute_url",
    "DoesNotExist",
    "MultipleObjectsReturned",
}

# Django template filters / tag fragments we never want to mistake for
# attribute access while parsing.
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


@dataclass
class Finding:
    file: str
    line: int
    chain: str
    severity: str  # "HARD" or "SOFT"
    reason: str

    def format(self) -> str:
        return (
            f"{self.severity}  {self.file}:{self.line}  {self.chain}  -- {self.reason}"
        )


# ---------------------------------------------------------------------------
# Template parsing
# ---------------------------------------------------------------------------

# Regex that captures the raw expression inside ``{{ ... }}`` and
# ``{% ... %}`` constructs. We post-process the body to extract the dotted
# chain(s) that look like ``foo.bar.baz`` (i.e. resolvable against the
# template context).
VARIABLE_RE = re.compile(r"\{\{\s*(.+?)\s*\}\}", re.DOTALL)
TAG_RE = re.compile(r"\{%\s*(.+?)\s*%\}", re.DOTALL)
FOR_RE = re.compile(r"for\s+([\w,\s]+?)\s+in\s+([\w\.]+)")

# A dotted chain candidate: identifier(.identifier)+ . We require at least one
# dot so that bare ``foo`` (which doesn't fail silently in any interesting
# way -- it's just rendered as the str()) is skipped.
CHAIN_RE = re.compile(r"\b([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)+)\b")


def iter_chains_with_lines(text: str) -> Iterable[tuple[int, str, dict[str, str]]]:
    """Yield ``(line, chain, loop_vars_so_far)`` for every dotted chain.

    ``loop_vars_so_far`` accumulates ``{% for X in Y %}`` bindings discovered
    earlier in the file. This is approximate: we don't track ``{% endfor %}``
    pop semantics; loops that share a variable name across the file will
    settle on the most recent binding. For an audit that's fine.
    """
    loop_vars: dict[str, str] = {}

    # Walk the file character by character, keeping a running line number.
    # We process ``{% ... %}`` and ``{{ ... }}`` in document order so that
    # for-loop bindings are seen before chains that use them.
    token_re = re.compile(r"\{[%{]\s*(.+?)\s*[%}]\}", re.DOTALL)
    for m in token_re.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        body = m.group(1)
        opening = text[m.start() : m.start() + 2]

        if opening == "{%":
            for_match = FOR_RE.search(body)
            if for_match:
                names = [n.strip() for n in for_match.group(1).split(",") if n.strip()]
                collection = for_match.group(2)
                # Decide the element type. Prefer the table; otherwise fall
                # back to "drop the trailing 's'" heuristic; otherwise leave
                # untyped (None).
                collection_root = collection.split(".")[0]
                model_name = COLLECTION_TO_MODEL.get(collection_root)
                if model_name is None and collection_root in ROOT_TO_MODEL:
                    # ``for ukucanin in domacinstvo.ukucani.all`` etc. -- the
                    # collection root is a known root variable. We can't
                    # generally resolve ``.ukucani.all`` here, so leave the
                    # element type to the variable-name table.
                    pass
                for n in names:
                    if model_name:
                        loop_vars[n] = model_name
                    elif n in ROOT_TO_MODEL:
                        loop_vars[n] = ROOT_TO_MODEL[n]
            # Tag bodies often reference variables (``{% if foo.bar %}``,
            # ``{% url 'x' uid=obj.adresa.ulica %}``). Treat them like a
            # variable expression.
            for chain_match in CHAIN_RE.finditer(body):
                yield line, chain_match.group(1), dict(loop_vars)
        else:
            # ``{{ ... }}`` -- one or more chains, possibly with filters.
            # Strip filter pipes and their arguments before scanning.
            cleaned = strip_filters(body)
            for chain_match in CHAIN_RE.finditer(cleaned):
                yield line, chain_match.group(1), dict(loop_vars)


def strip_filters(expr: str) -> str:
    """Drop filter pipes from a variable expression body.

    ``foo.bar|default:"x"|length`` becomes ``foo.bar``. Filter names and their
    arguments are not attribute chains; ignoring them avoids false positives.
    """
    # Split on '|', keep the first segment.
    return expr.split("|", 1)[0]


# ---------------------------------------------------------------------------
# Model walk
# ---------------------------------------------------------------------------


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

    The caller decides severity.
    """
    if attr in TEMPLATE_BUILTINS:
        return "scalar", None

    # Try the Django field cache first -- it's authoritative.
    try:
        field = model._meta.get_field(attr)
    except Exception:
        field = None

    # Attributes added at runtime via ``Prefetch(to_attr="prefetched_xxx")``
    # are invisible to ``_meta.get_field`` and to ``dir(cls)``. By convention
    # all our prefetch annotations are named ``prefetched_*`` (see e.g.
    # ``parohijan_view.SpisakParohijana``); treat them as opaque querysets so
    # the audit doesn't crow about a real-but-dynamic attribute.
    # View-annotated attributes computed in the view loop (not via
    # Prefetch(to_attr=...), so not prefetched_*-prefixed): e.g.
    # Domacinstvo.zivi_clanovi / preminuli_clanovi set in
    # domacinstvo_view / slava_view and guarded with {% if %} in templates.
    if attr.startswith("prefetched_") or attr in {"zivi_clanovi", "preminuli_clanovi"}:
        return "queryset", None

    if field is not None:
        if isinstance(field, (ForeignKey, OneToOneField)):
            return "model", field.related_model
        if isinstance(field, ManyToManyField):
            return "queryset", field.related_model
        if isinstance(field, ForeignObjectRel):
            # Reverse relation. One-to-one is a model; the rest are querysets.
            if field.one_to_one:
                return "model", field.related_model
            return "queryset", field.related_model
        return "scalar", field

    # Fall back to Python attribute lookup.
    cls_attr = getattr(model, attr, None)
    if cls_attr is None:
        return "missing", None
    if isinstance(cls_attr, property):
        return "property", None
    if callable(cls_attr):
        return "property", None
    return "property", None


def walk(model: type[Model], parts: list[str]) -> tuple[str, str] | None:
    """Walk a chain rooted at ``model``.

    Returns ``None`` if everything resolves cleanly. Otherwise returns
    ``(severity, reason)``.
    """
    current_kind = "model"
    current_target: object = model

    for i, attr in enumerate(parts):
        if current_kind != "model":
            # We're trying to access ``.attr`` on something that isn't a
            # model. Decide severity by what we landed on at the previous
            # step.
            if current_kind == "scalar":
                # The chain accesses an attribute on a non-relational field.
                # This is the classic bug (CharField.naziv, DateField.year is
                # OK but not auditable -- still report so the human can decide).
                # Allow a tiny whitelist of well-known datetime attrs.
                if attr in {"year", "month", "day", "hour", "minute", "second"}:
                    return None
                # Allow ``.url`` on file/image fields -- handled later if
                # needed. For now, hard.
                field = current_target
                ftype = type(field).__name__ if field is not None else "scalar"
                return (
                    "HARD",
                    f"step '{attr}' accesses attribute on {ftype} "
                    f"(parent: {'.'.join(parts[:i])})",
                )
            if current_kind == "queryset":
                if attr in QUERYSET_TERMINALS:
                    # ``foo.bar.all`` etc. is the terminal; anything further
                    # we can't really judge.
                    return None
                # ``parohijan.prefetched_ukucanstva.0`` -- numeric index into a
                # Python list. Template-resolvable, opaque to introspection.
                if attr.isdigit():
                    return None
                # ``foo.related.attr`` -- can't iterate without query; soft.
                return (
                    "SOFT",
                    f"step '{attr}' on queryset (parent: {'.'.join(parts[:i])})",
                )
            if current_kind == "property":
                # Can't know the property's return type. Soft.
                return (
                    "SOFT",
                    f"step '{attr}' after property/method "
                    f"(parent: {'.'.join(parts[:i])})",
                )

        kind, target = step(current_target, attr)  # type: ignore[arg-type]
        if kind == "missing":
            return (
                "HARD",
                f"step '{attr}' not found on " f"{current_target.__name__}",  # type: ignore[union-attr]
            )
        current_kind, current_target = kind, target

    return None


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


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
            base = Path(settings.BASE_DIR)
            templates_dir = base / "registar" / "templates"
        templates_dir = Path(templates_dir)

        if not templates_dir.exists():
            self.stderr.write(f"Templates dir not found: {templates_dir}")
            return

        findings: list[Finding] = []
        chains_checked = 0

        for html in sorted(templates_dir.rglob("*.html")):
            text = html.read_text(encoding="utf-8")
            for line, chain, loop_vars in iter_chains_with_lines(text):
                parts = chain.split(".")
                root = parts[0]

                # Skip obvious non-context references: ``request.user.x``,
                # ``form.x``, ``view.x``, template-tag positional args, etc.
                if root in {
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
                }:
                    continue

                # Skip filter argument fragments like ``default:"foo.bar"``.
                if root in TEMPLATE_FILTER_TOKENS:
                    continue

                model_name = loop_vars.get(root) or ROOT_TO_MODEL.get(root)
                if not model_name:
                    continue  # Unknown root -- skip silently.

                model = resolve_model(model_name)
                if model is None:
                    continue

                chains_checked += 1
                result = walk(model, parts[1:])
                if result is None:
                    continue
                severity, reason = result
                if opts["severity"] != "ALL" and severity != opts["severity"]:
                    continue

                rel_path = html.relative_to(templates_dir.parent)
                findings.append(
                    Finding(
                        file=str(rel_path),
                        line=line,
                        chain=chain,
                        severity=severity,
                        reason=reason,
                    )
                )

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
