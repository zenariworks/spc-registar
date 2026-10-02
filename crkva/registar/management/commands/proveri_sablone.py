"""Ревизија Django шаблона: ланци атрибута које шема модела не може да разреши.

Шаблон `{{ obj.foo.bar }}` рендерује празан стринг кад `.bar` не постоји на
`foo`. Ова команда пролази кроз све шаблоне у `crkva/registar/templates/`,
издваја сваки ланац са тачкама, тип коренске променљиве закључује из мале
табеле (уз закључивање из `{% for X in Y %}` петљи) и пријављује ланце који се
не могу разрешити према шеми Django модела.

Две тежине налаза:

* ``HARD``  -- корен ланца је познат модел, а бар један корак је сигурно
  погрешан (нпр. атрибут на ``CharField``-у, непостојећи атрибут/својство
  модела, погрешан назив обрнуте везе).
* ``SOFT``  -- корен је познат модел, али ревизија не може да прође цео ланац
  (нпр. прешла је преко својства чији тип повратне вредности није познат).
  Само као контекст; намерно бучно.

Команда је намерно приближна: боље лажно упозорење него пропуштена грешка.
Циљ је списак за преглед, а не капија која одбија измене.
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
"""Табела коренских променљивих: назив променљиве у шаблону → модел у ``registar``.

Променљиве петљи из ``{% for X in Y %}`` додају се успут; ова табела је
резерва за контекст који шаљу прикази. ``entry`` и ``change`` из
``_history_panel.html`` су dataclass-ови HistoryEntry / FieldChange (види
``registar/istorija.py``), а не Django модели, па су намерно изостављени --
ревизија не може да прочита поља dataclass-а и пријавила би сваки приступ.
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
"""Назив колекције петље → модел елемента, за тип ``X`` у ``{% for X in Y %}``."""

QUERYSET_TERMINALS = {"all", "count", "first", "last", "exists", "filter", "exclude"}
"""Атрибути QuerySet-а / Manager-а на којима пролаз стаје, без упита у базу."""

TEMPLATE_BUILTINS = {
    "pk",
    "id",
    "uid",
    "get_absolute_url",
    "DoesNotExist",
    "MultipleObjectsReturned",
}
"""Псеудо-атрибути које сваки модел у пракси има; пролаз на њима стаје."""

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
"""Делови филтера / тагова које не треба сматрати приступом атрибуту."""

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
"""Коренови који нису контекст модела: ``request.user.x``, ``form.x``, ``view.x`` …"""

DATETIME_ATTRS = {"year", "month", "day", "hour", "minute", "second"}
"""Атрибути дозвољени на пољима датума/времена."""

VIEW_ANNOTATED_QUERYSETS = {"zivi_clanovi", "preminuli_clanovi"}
"""Спискови које прикази у петљи качe на Domacinstvo (domacinstvo_view, slava_view).

Нису ``Prefetch(to_attr=...)`` атрибути, па немају префикс ``prefetched_``, а
шаблони их чувају са ``{% if %}``.
"""

TOKEN_RE = re.compile(r"\{[%{]\s*(.+?)\s*[%}]\}", re.DOTALL)
"""Конструкција ``{{ ... }}`` или ``{% ... %}``; група 1 је њено тело."""

FOR_RE = re.compile(r"for\s+([\w,\s]+?)\s+in\s+([\w\.]+)")

CHAIN_RE = re.compile(r"\b([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)+)\b")
"""Ланац са тачкама ``foo.bar(.baz)*``; само ``foo`` се прескаче јер не може тихо да омане."""


@dataclass
class Finding:
    """Један пријављени ланац; ``severity`` је ``"HARD"`` или ``"SOFT"``."""

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
    """Даје ``(line, chain, loop_vars_so_far)`` за сваки ланац са тачкама.

    Тагови и променљиве се обрађују редом из документа, па се везивања из
    ``{% for X in Y %}`` виде пре ланаца који их користе. ``loop_vars_so_far``
    скупља та везивања. Ово је приближно: ``{% endfor %}`` се не прати, па
    петље које у истом фајлу деле назив променљиве задржавају последње
    везивање. За ревизију је то довољно.

    Тело тага се претражује цело (``{% if foo.bar %}``,
    ``{% url 'x' uid=obj.adresa.ulica %}``), а телу променљиве се прво
    уклањају филтери.
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
    """Додељује тип називима из тага ``{% for %}``.

    Предност има табела колекција; иначе променљива петље која је и сама
    познат назив корена (``for ukucanin in domacinstvo.ukucani.all``) задржава
    тај тип. Све остало остаје без типа.
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
    """Уклања филтере из тела израза променљиве.

    ``foo.bar|default:"x"|length`` постаје ``foo.bar``. Називи филтера и
    њихови аргументи нису ланци атрибута; њихово занемаривање спречава лажна
    упозорења.
    """
    return expr.split("|", 1)[0]


def resolve_model(name: str) -> type[Model] | None:
    """Класа модела по кратком називу у апликацији ``registar``."""
    try:
        return apps.get_model("registar", name)
    except LookupError:
        return None


def step(model: type[Model], attr: str) -> tuple[str, object]:
    """Један корак дуж ланца са тачкама.

    Враћа ``(kind, target)``, где је ``kind`` једно од:

    * ``"model"`` -- други модел; ``target`` је класа модела
    * ``"scalar"`` -- поље које није веза; ``target`` је инстанца поља
    * ``"queryset"`` -- обрнута FK / M2M веза; ``target`` је модел елемента
    * ``"property"`` -- својство/метода коју не можемо да испитамо;
      ``target`` је ``None``
    * ``"missing"`` -- атрибут не постоји на моделу

    Атрибути додати у току рада преко ``Prefetch(to_attr="prefetched_xxx")``
    невидљиви су за ``_meta.get_field`` и ``dir(cls)``; по договору сви носе
    назив ``prefetched_*`` и третирају се као непрозирни queryset-ови, као и
    спискови које додају прикази. Тежину одређује позивалац.
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
    """Резултат ``step`` за Django поље; обрнута веза један-на-један је модел."""
    if isinstance(field, (ForeignKey, OneToOneField)):
        return "model", field.related_model
    if isinstance(field, ManyToManyField):
        return "queryset", field.related_model
    if isinstance(field, ForeignObjectRel):
        return ("model" if field.one_to_one else "queryset"), field.related_model
    return "scalar", field


def walk(model: type[Model], parts: list[str]) -> tuple[str, str] | None:
    """Пролаз кроз ланац са кореном у ``model``.

    Враћа ``None`` ако се све уредно разреши, иначе ``(severity, reason)``.
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
    """Оцена ``.attr`` на нечему што није модел.

    * скалар -- класична грешка (``CharField.naziv``) је HARD; неколико
      атрибута датума/времена је дозвољено.
    * queryset -- завршни атрибути (``.all``) и бројчани индекси списка
      (``prefetched_ukucanstva.0``) завршавају пролаз; за све остало треба
      упит, па SOFT.
    * својство/метода -- тип повратне вредности није познат, па SOFT.
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
    """Модел коренске променљиве ланца, или None ако се корен не проверава."""
    root = chain.split(".")[0]
    if root in SKIP_ROOTS or root in TEMPLATE_FILTER_TOKENS:
        return None
    model_name = loop_vars.get(root) or ROOT_TO_MODEL.get(root)
    if not model_name:
        return None
    return resolve_model(model_name)


def audit_template(text: str, file: str, severity: str) -> tuple[list[Finding], int]:
    """Налази једног шаблона (по ``severity``) и број проверених ланаца."""
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
    help = "Ревизија registar шаблона: ланци атрибута које модел не може да разреши."

    def add_arguments(self, parser):
        parser.add_argument(
            "--templates-dir",
            default=None,
            help="Други корен шаблона (подразумевано crkva/registar/templates).",
        )
        parser.add_argument(
            "--severity",
            choices=["HARD", "SOFT", "ALL"],
            default="ALL",
            help="Филтер налаза по тежини (подразумевано ALL).",
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
        """Прво бројеви, па HARD налази, па SOFT налази."""
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
