#!/usr/bin/env python3
"""Block <style> blocks and inline style="..." in HTML templates.

Why: any styling in HTML bypasses our design-token system. The
hardcoded-color hook only scans .css files, so colors inside
<style> tags slip through. Inline styles also fight theme
overrides and make components hard to restyle.

Exempted (legitimate inline-style use cases):
  - pdf_*.html        — WeasyPrint-rendered PDFs use mm-based inline layout
  - calibrate_*.html  — coord-calibration tooling overlays on a bg image

Escape hatch for one-off cases: add either
    {# style-allow #}
    <!-- style-allow -->
on the same line as the offending tag/attribute. Use sparingly,
e.g. when a value must be computed from template context.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>", re.IGNORECASE)
INLINE_STYLE_RE = re.compile(r'''\bstyle\s*=\s*["']''')
ALLOW_MARKER = re.compile(r"(\{#\s*style-allow\s*#\}|<!--\s*style-allow\s*-->)")

EXEMPT_PREFIXES = ("pdf_", "calibrate_")


def is_exempt(path: Path) -> bool:
    return path.name.startswith(EXEMPT_PREFIXES)


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings
    for ln, raw in enumerate(text.splitlines(), 1):
        if ALLOW_MARKER.search(raw):
            continue
        if STYLE_BLOCK_RE.search(raw):
            findings.append((ln, "<style> block", raw.strip()))
            continue
        if INLINE_STYLE_RE.search(raw):
            findings.append((ln, 'style="..." attribute', raw.strip()))
    return findings


def main(argv: list[str]) -> int:
    if argv:
        paths = [Path(a) for a in argv]
    else:
        base = Path("crkva")
        paths = list(base.rglob("*.html"))
    paths = [p for p in paths if p.suffix == ".html"]
    violations: list[tuple[Path, list[tuple[int, str, str]]]] = []
    for p in paths:
        if is_exempt(p):
            continue
        findings = scan_file(p)
        if findings:
            violations.append((p, findings))
    if not violations:
        return 0
    print("Styles found inline in HTML templates (move them to CSS):")
    print()
    for path, findings in violations:
        for ln, kind, snippet in findings:
            short = snippet[:140] + ("..." if len(snippet) > 140 else "")
            print(f"  {path}:{ln}  [{kind}]")
            print(f"      {short}")
    print()
    print("Move styles to crkva/registar/static/registar/components/ or themes/.")
    print("If a value MUST be dynamic, add `{# style-allow #}` on the same line.")
    print("Exempt: pdf_*.html, calibrate_*.html (WeasyPrint / overlay tooling).")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
