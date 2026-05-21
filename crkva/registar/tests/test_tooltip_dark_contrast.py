"""Regression tests for the dark-mode tooltip contrast bug.

Bug history: tooltips (`[data-tooltip]::after`, sidebar collapsed tooltips,
`.fasting-tooltip`) rendered dark text on a dark bubble in dark mode because
they consumed `var(--color-surface)` for `color` while `--color-surface`
resolves to the page background (#0d1117) in dark mode.

The fix introduces dedicated, theme-aware tokens (`--tooltip-bg`,
`--tooltip-text`, `--tooltip-shadow`) defined in `themes/svetla.css` for the
light theme and overridden in `themes/tamna.css` for the dark theme. All
tooltip variants must consume those tokens — never `--color-surface` or
`--color-text` — so their values can never collide with the page bg.

The tests below pin both the token contract and the consuming rules.
"""

from __future__ import annotations

import pathlib
import re

from django.test import TestCase


# Resolve relative to this test file so cwd doesn't matter (manage.py test runs
# from `crkva/`, pytest may run from repo root).
_REGISTAR_APP_DIR = pathlib.Path(__file__).resolve().parent.parent
REGISTAR_STATIC = _REGISTAR_APP_DIR / "static" / "registar"
TOKENS_CSS = REGISTAR_STATIC / "themes" / "svetla.css"
DARK_THEME_CSS = REGISTAR_STATIC / "themes" / "tamna.css"
DUGMAD_CSS = REGISTAR_STATIC / "components" / "dugmad.css"
SIDEBAR_CSS = REGISTAR_STATIC / "layout" / "bocna-traka.css"
KALENDAR_CSS = REGISTAR_STATIC / "pages" / "kalendar.css"


def _iter_rule_bodies(css_text: str, selector_substring: str):
    """Yield bodies of every top-level CSS rule whose selector contains the substring.

    Naive but adequate for our flat, hand-written CSS. Handles multi-line
    selectors (comma-separated) and ignores nested at-rules — top-level only.
    """
    # Walk top-level `{ ... }` blocks. We track brace depth so we skip nested
    # rules inside @media / @supports etc.
    i = 0
    depth = 0
    sel_start = 0
    n = len(css_text)
    while i < n:
        ch = css_text[i]
        if ch == "{":
            if depth == 0:
                selector = css_text[sel_start:i]
                # find matching close
                body_start = i + 1
                j = body_start
                inner_depth = 1
                while j < n and inner_depth:
                    if css_text[j] == "{":
                        inner_depth += 1
                    elif css_text[j] == "}":
                        inner_depth -= 1
                    j += 1
                body = css_text[body_start : j - 1]
                # Normalise selector (collapse whitespace) before checking
                sel_norm = re.sub(r"\s+", " ", selector).strip()
                if selector_substring in sel_norm:
                    yield sel_norm, body
                i = j
                sel_start = i
                continue
            else:
                depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
            sel_start = i + 1
        i += 1


def _rule_body(css_text: str, selector_substring: str) -> str:
    """Return the body of the first matching rule that actually styles colors.

    Filters out rules that only set layout (e.g., mobile @media tweaks that
    just change `font-size` on `.fasting-tooltip`) so the consumer assertion
    targets the rule with `background`/`color` declarations.
    """
    matches = list(_iter_rule_bodies(css_text, selector_substring))
    assert matches, f"selector containing {selector_substring!r} not found"
    # Prefer the first match that declares `background` or `color`
    for _sel, body in matches:
        if "background" in body or "color:" in body:
            return body
    # Fallback to the first match
    return matches[0][1]


def _token_value(css_text: str, scope_selector: str, token_name: str) -> str:
    """Return the value of `--token-name` inside the first `scope_selector { ... }` block."""
    # Find the block opening
    idx = css_text.find(scope_selector)
    assert idx >= 0, f"scope selector {scope_selector!r} not found"
    # Find the next `{` and matching `}` (no nested braces in our token blocks)
    open_brace = css_text.find("{", idx)
    close_brace = css_text.find("}", open_brace)
    block = css_text[open_brace + 1 : close_brace]
    m = re.search(rf"{re.escape(token_name)}\s*:\s*([^;]+);", block)
    assert m is not None, f"{token_name} not declared in {scope_selector}"
    return m.group(1).strip()


class TooltipTokenContractTests(TestCase):
    """The dedicated tooltip tokens must exist in both themes with distinct values."""

    def test_light_theme_defines_tooltip_tokens(self):
        text = TOKENS_CSS.read_text(encoding="utf-8")
        bg = _token_value(text, ":root", "--tooltip-bg")
        fg = _token_value(text, ":root", "--tooltip-text")
        # Both must be present
        self.assertTrue(bg, "--tooltip-bg must be set in light theme")
        self.assertTrue(fg, "--tooltip-text must be set in light theme")
        # And must differ — otherwise the bubble is invisible
        self.assertNotEqual(
            bg.lower(),
            fg.lower(),
            "light tooltip bg and text must differ to be readable",
        )

    def test_dark_theme_overrides_tooltip_tokens(self):
        text = DARK_THEME_CSS.read_text(encoding="utf-8")
        bg = _token_value(text, ':root[data-theme="dark"]', "--tooltip-bg")
        fg = _token_value(text, ':root[data-theme="dark"]', "--tooltip-text")
        self.assertTrue(bg, "--tooltip-bg must be overridden in dark theme")
        self.assertTrue(fg, "--tooltip-text must be overridden in dark theme")
        self.assertNotEqual(
            bg.lower(),
            fg.lower(),
            "dark tooltip bg and text must differ to be readable",
        )

    def test_dark_tooltip_text_is_not_page_surface(self):
        """The original bug: tooltip color was --color-surface, which is #0d1117 in dark.

        Lock that down — the dark tooltip text must NOT match the page bg.
        """
        text = DARK_THEME_CSS.read_text(encoding="utf-8")
        surface = _token_value(text, ':root[data-theme="dark"]', "--color-surface")
        fg = _token_value(text, ':root[data-theme="dark"]', "--tooltip-text")
        self.assertNotEqual(
            fg.lower(),
            surface.lower(),
            "dark tooltip text must differ from page --color-surface",
        )

    def test_dark_tooltip_bg_differs_from_text_color_token(self):
        """Belt-and-suspenders: tooltip bg must not match --color-text either."""
        text = DARK_THEME_CSS.read_text(encoding="utf-8")
        color_text = _token_value(text, ':root[data-theme="dark"]', "--color-text")
        bg = _token_value(text, ':root[data-theme="dark"]', "--tooltip-bg")
        self.assertNotEqual(
            bg.lower(),
            color_text.lower(),
            "tooltip bg must differ from --color-text",
        )


class TooltipConsumerTests(TestCase):
    """Every tooltip selector must consume --tooltip-* tokens, never the
    theme-aware --color-surface / --color-text tokens (which caused the bug)."""

    BANNED_FOR_TOOLTIPS = ("var(--color-surface)", "var(--color-text)")

    def _assert_tooltip_rule(self, css_text: str, selector: str) -> None:
        body = _rule_body(css_text, selector)
        self.assertIn(
            "var(--tooltip-bg)",
            body,
            f"{selector} must use var(--tooltip-bg) for background",
        )
        self.assertIn(
            "var(--tooltip-text)",
            body,
            f"{selector} must use var(--tooltip-text) for color",
        )
        for banned in self.BANNED_FOR_TOOLTIPS:
            self.assertNotIn(
                banned,
                body,
                f"{selector} must NOT use {banned} — it inverts in dark mode",
            )

    def test_data_tooltip_after_uses_tokens(self):
        text = DUGMAD_CSS.read_text(encoding="utf-8")
        self._assert_tooltip_rule(text, "[data-tooltip]::after")

    def test_sidebar_aria_label_tooltip_uses_tokens(self):
        text = SIDEBAR_CSS.read_text(encoding="utf-8")
        # The aria-label tooltip rule uses .sidebar-action-btn:hover::after
        self._assert_tooltip_rule(text, ".sidebar-action-btn:hover::after")

    def test_sidebar_title_tooltip_uses_tokens(self):
        text = SIDEBAR_CSS.read_text(encoding="utf-8")
        # The title tooltip rule uses .sidebar-menu-item > a:hover::after
        self._assert_tooltip_rule(text, ".sidebar-menu-item > a:hover::after")

    def test_fasting_tooltip_uses_tokens(self):
        text = KALENDAR_CSS.read_text(encoding="utf-8")
        self._assert_tooltip_rule(text, ".fasting-tooltip")


class TooltipBundleTests(TestCase):
    """Sanity check that the compressed bundle (if present) reflects the fix.

    The source-file tests above are authoritative. This test only fires
    when there is a freshly built bundle (newer than the source CSS) on
    disk — that's the post-deploy verification path; on dev/CI it skips.
    """

    def test_bundled_css_contains_tooltip_tokens(self):
        cache_dir = pathlib.Path("/vol/web/static/CACHE/css")
        if not cache_dir.exists():
            self.skipTest("no compressed CSS bundle on this machine")
        bundles = sorted(
            cache_dir.glob("output.*.css"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        # Find the most recent bundle that actually contains tooltip rules
        tooltip_bundle = next(
            (b for b in bundles if "data-tooltip" in b.read_text(encoding="utf-8")),
            None,
        )
        if tooltip_bundle is None:
            self.skipTest("no bundle currently contains tooltip rules")
        # Skip when the bundle pre-dates the source — it's just stale, not
        # broken. After deploy (collectstatic), the new bundle will be
        # written and this test will assert the right contents.
        source_mtime = max(
            DUGMAD_CSS.stat().st_mtime,
            SIDEBAR_CSS.stat().st_mtime,
            KALENDAR_CSS.stat().st_mtime,
            TOKENS_CSS.stat().st_mtime,
            DARK_THEME_CSS.stat().st_mtime,
        )
        if tooltip_bundle.stat().st_mtime < source_mtime:
            self.skipTest(
                "tooltip CSS bundle is older than source — run collectstatic"
            )
        text = tooltip_bundle.read_text(encoding="utf-8")
        # Bundle must reference the new tokens, not the broken --color-surface
        self.assertIn("--tooltip-bg", text)
        self.assertIn("--tooltip-text", text)
