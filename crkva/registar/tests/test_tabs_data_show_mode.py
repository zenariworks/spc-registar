"""Regression tests for tabs `data-show-mode` placement on krstenje / vencanje.

Background
----------
The outer ``<div class="tabs tabs--segmented">`` wrapper on ``krstenje.html`` and
``vencanje.html`` was twice tagged ``data-show-mode="view"``. Under the CSS rule

    [data-mode="edit"] [data-show-mode="view"] { display: none !important; }

that hid the entire editable form when the user clicked "Измени" (the form's
``data-mode`` flipped to ``edit`` and the whole tabs wrapper, including the
data-panel with the editable info-row inputs, disappeared).

The fix: only the ``.tabs__nav`` (the segmented tab switcher) and the
certificate-preview ``<section class="tabs__panel">`` may carry
``data-show-mode="view"``. The outer wrapper must NOT, and the data-panel
``<section class="tabs__panel">`` (which hosts the editable info-section panels)
must NOT either.

History:
- PR #140 / commit 994cd58 — original fix.
- PR #141 — template refactor regressed it.
- PR #143 / commit c4827d5 — re-fix after the refactor.

This module pins the contract three ways so future regressions get caught:

1. Static template scan — the substring contract.
2. Rendered-HTML assertion in edit mode — the actual served document is sane.
3. CSS contract sanity — the rule that makes (1) and (2) meaningful still exists.
"""

# pylint: disable=missing-function-docstring

from __future__ import annotations

import datetime
import pathlib
import re

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from registar.models import Krstenje, Osoba, Vencanje
from tenants.models import Role, Tenant, UserMembership

User = get_user_model()

# Resolve relative to this test file so cwd doesn't matter (manage.py test runs
# from `crkva/`, pytest may run from repo root).
_REGISTAR_APP_DIR = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES_DIR = _REGISTAR_APP_DIR / "templates" / "registar"
KRSTENJE_TEMPLATE = TEMPLATES_DIR / "krstenje.html"
VENCANJE_TEMPLATE = TEMPLATES_DIR / "vencanje.html"
INFO_CSS = _REGISTAR_APP_DIR / "static" / "registar" / "components" / "info.css"


class TabsDataShowModeRegressionTests(TestCase):
    """Pin `data-show-mode` placement on the krstenje/vencanje tabs wrappers.

    See module docstring for the PR #140 / PR #143 history.
    """

    # ------------------------------------------------------------------
    # Fixtures (mirrors test_krstenje_full_name_render and test_vencanje_toggle).
    # ------------------------------------------------------------------
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.get(schema_name="test_tenant")
        cls.clerk = User.objects.create_user(username="kanc-tabs", password="x")
        UserMembership.objects.create(
            user=cls.clerk, tenant=cls.tenant, role=Role.KANCELARIJA
        )

        # Krstenje fixtures.
        cls.dete = Osoba.objects.create(ime="Дете", prezime="Презименко", pol="М")
        cls.otac = Osoba.objects.create(ime="Отац", prezime="Презименко", pol="М")
        cls.majka = Osoba.objects.create(ime="Мајка", prezime="Презименко", pol="Ж")
        cls.kum = Osoba.objects.create(ime="Кум", prezime="Кумовић", pol="М")
        cls.krstenje = Krstenje.objects.create(
            dete=cls.dete,
            otac=cls.otac,
            majka=cls.majka,
            kum=cls.kum,
            datum=datetime.date(2020, 1, 1),
            knjiga="1",
            strana="2",
            broj="3",
            godina_registracije=2020,
            redni_broj=1,
            dete_vanbracno=False,
            dete_blizanac=False,
            dete_sa_telesnom_manom=False,
        )

        # Vencanje fixtures.
        cls.zenik = Osoba.objects.create(ime="Жеља", prezime="Жељовић", pol="М")
        cls.nevesta = Osoba.objects.create(ime="Нада", prezime="Надовић", pol="Ж")
        cls.vencanje = Vencanje.objects.create(
            zenik=cls.zenik,
            nevesta=cls.nevesta,
            datum=datetime.date(2020, 6, 6),
            knjiga="1",
            strana="1",
            broj="1",
            redni_broj=1,
            godina_registracije=2020,
            razresenje=False,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.clerk)

    # ------------------------------------------------------------------
    # Helpers.
    # ------------------------------------------------------------------
    def _find_ancestor_with_view_gate(self, html: str, needle: str) -> str | None:
        """Return the first ancestor opening tag that has ``data-show-mode="view"``.

        Walks backwards from ``needle`` through every still-open ancestor tag in
        ``html`` (a simple bracket-balanced scan, adequate for Django's
        well-formed templates). Returns the tag string, or ``None`` if no
        ancestor is view-gated.
        """
        idx = html.find(needle)
        if idx < 0:
            return None  # caller will assert presence separately
        # Track open tags via depth counting from the start of the document.
        # Each non-self-closing, non-void opening tag pushes onto the stack;
        # each closing tag pops.
        tag_re = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)\b([^>]*)>")
        void_tags = {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
        stack: list[tuple[str, str]] = []  # (tag_name, full_opening_tag)
        for match in tag_re.finditer(html):
            if match.start() >= idx:
                break
            closing, name, attrs = (
                match.group(1),
                match.group(2).lower(),
                match.group(3),
            )
            full = match.group(0)
            if closing:
                # Pop matching tag if present.
                for k in range(len(stack) - 1, -1, -1):
                    if stack[k][0] == name:
                        del stack[k:]
                        break
                continue
            if name in void_tags:
                continue
            if attrs.rstrip().endswith("/"):
                continue
            stack.append((name, full))
        for _name, full in stack:
            if 'data-show-mode="view"' in full:
                return full
        return None

    # ------------------------------------------------------------------
    # Layer 1 — static template scan.
    # ------------------------------------------------------------------
    def test_krstenje_outer_tabs_wrapper_is_not_view_gated(self):
        # Regression guard for PR #140 / PR #143: the outer
        # `<div class="tabs tabs--segmented">` must NOT carry data-show-mode,
        # otherwise [data-mode="edit"] hides the whole editable form.
        body = KRSTENJE_TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn(
            'class="tabs tabs--segmented" data-show-mode',
            body,
            "Outer tabs wrapper on krstenje.html must not be view-gated; "
            "would re-introduce the PR #140 / #143 regression hiding the edit form.",
        )

    def test_vencanje_outer_tabs_wrapper_is_not_view_gated(self):
        # Same regression guard for vencanje.html — see PR #140 / PR #143.
        body = VENCANJE_TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn(
            'class="tabs tabs--segmented" data-show-mode',
            body,
            "Outer tabs wrapper on vencanje.html must not be view-gated; "
            "would re-introduce the PR #140 / #143 regression hiding the edit form.",
        )

    def test_krstenje_tabs_nav_is_view_gated(self):
        # Positive half of the PR #140 / #143 contract: the segmented tab
        # switcher (`.tabs__nav`) must be hidden in edit mode, otherwise the
        # tab radios bleed into the editable form.
        body = KRSTENJE_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            'class="tabs__nav" data-show-mode="view"',
            body,
            ".tabs__nav on krstenje.html must carry data-show-mode='view'.",
        )

    def test_vencanje_tabs_nav_is_view_gated(self):
        # Same positive half of the PR #140 / #143 contract for vencanje.
        body = VENCANJE_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            'class="tabs__nav" data-show-mode="view"',
            body,
            ".tabs__nav on vencanje.html must carry data-show-mode='view'.",
        )

    # ------------------------------------------------------------------
    # Layer 2 — rendered-HTML assertion in edit mode.
    # ------------------------------------------------------------------
    def _assert_edit_mode_keeps_data_panel_visible(
        self, url: str, editable_field_name: str
    ) -> None:
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, f"GET {url} -> {r.status_code}")
        body = r.content.decode("utf-8")

        # Form is in edit mode.
        self.assertIn(
            "data-edit-toggle-root",
            body,
            "form root marker missing from rendered HTML",
        )
        self.assertIn(
            'data-mode="edit"',
            body,
            "form must render with data-mode='edit' on /izmena/",
        )

        # The outer `<div class="tabs tabs--segmented">` opening tag (which can
        # span multiple lines) must not carry data-show-mode anywhere in its
        # attribute list. Match the literal tag opener and consume until '>'.
        tabs_open = re.search(r'<div\b[^>]*class="tabs tabs--segmented"[^>]*>', body)
        self.assertIsNotNone(
            tabs_open,
            "outer <div class='tabs tabs--segmented'> not found in rendered HTML",
        )
        self.assertNotIn(
            "data-show-mode",
            tabs_open.group(0),
            "Outer tabs wrapper rendered with data-show-mode — PR #140 / #143 "
            "regression: editable form will be hidden by the CSS rule "
            "[data-mode='edit'] [data-show-mode='view'] { display: none !important; }.",
        )

        # The editable input is present AND has no view-gated ancestor.
        input_pattern = re.compile(
            r'<input\b[^>]*\bname="' + re.escape(editable_field_name) + r'"[^>]*>'
        )
        m = input_pattern.search(body)
        self.assertIsNotNone(
            m,
            f"editable <input name='{editable_field_name}'> missing from rendered HTML",
        )
        gated = self._find_ancestor_with_view_gate(body, m.group(0))
        self.assertIsNone(
            gated,
            f"editable <input name='{editable_field_name}'> has a view-gated "
            f"ancestor: {gated!r}. That ancestor will be hidden by "
            "[data-mode='edit'] [data-show-mode='view'] — PR #140 / #143 regression.",
        )

    def test_krstenje_edit_mode_keeps_data_panel_visible(self):
        # PR #140 / #143: opening /izmena/krstenje/<uid>/ must keep the
        # editable info-row inputs visible (not nested under data-show-mode='view').
        url = reverse("izmena_krstenja", kwargs={"uid": self.krstenje.uid})
        self._assert_edit_mode_keeps_data_panel_visible(url, "redni_broj")

    def test_vencanje_edit_mode_keeps_data_panel_visible(self):
        # PR #140 / #143: opening /izmena/vencanje/<uid>/ must keep the
        # editable info-row inputs visible (not nested under data-show-mode='view').
        url = reverse("izmena_vencanja", kwargs={"uid": self.vencanje.uid})
        self._assert_edit_mode_keeps_data_panel_visible(url, "knjiga")

    # ------------------------------------------------------------------
    # Layer 3 — CSS contract sanity.
    # ------------------------------------------------------------------
    def test_info_css_data_mode_rules_exist(self):
        # The whole point of PR #140 / PR #143 is that these CSS rules exist
        # and gate visibility by data-mode. If they ever get renamed or
        # removed, the static-template assertions above become meaningless,
        # so pin the contract here too.
        css = INFO_CSS.read_text(encoding="utf-8")

        # Whitespace-tolerant patterns (the rule may grow extra declarations
        # over time, but `display: none !important;` must remain).
        edit_view_rule = re.compile(
            r'\[data-mode="edit"\]\s+\[data-show-mode="view"\]\s*'
            r"\{[^}]*display\s*:\s*none\s*!important[^}]*\}"
        )
        view_edit_rule = re.compile(
            r'\[data-mode="view"\]\s+\[data-show-mode="edit"\]\s*'
            r"\{[^}]*display\s*:\s*none\s*!important[^}]*\}"
        )

        self.assertRegex(
            css,
            edit_view_rule,
            "info.css must keep the rule "
            '[data-mode="edit"] [data-show-mode="view"] { display: none !important; } '
            "— removing it silently breaks the PR #140 / #143 contract.",
        )
        self.assertRegex(
            css,
            view_edit_rule,
            "info.css must keep the rule "
            '[data-mode="view"] [data-show-mode="edit"] { display: none !important; } '
            "— removing it silently breaks the PR #140 / #143 contract.",
        )
