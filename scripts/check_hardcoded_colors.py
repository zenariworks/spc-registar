#!/usr/bin/env python3
"""Block hardcoded hex colors in component CSS — they bypass theming.

Allowed locations for raw hex:
  - crkva/registar/static/registar/base/tokens.css   (canonical palette)
  - crkva/registar/static/registar/themes/*.css      (theme overrides)

Allowed values everywhere (affordance colors):
  - #fff / #ffffff   (white knob on toggle switches, text on red buttons)
  - #000 / #000000   (true black, rarely used)

Everything else under components/, layout/, utilities/, pages/ must
reference a `var(--color-*)` token so themes (light / sepia / dark)
can override it. Run by pre-commit on staged .css files.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b")
ALLOWED_VALUES = {"#fff", "#ffffff", "#000", "#000000"}
# Path fragments where raw hex is OK (the canonical palette + theme overrides)
ALLOWED_PATH_FRAGMENTS = (
    "/base/tokens.css",
    "/themes/",
    "/print/",  # print stylesheets target paper — fixed colors are fine
)

def is_allowed_file(path: Path) -> bool:
    s = str(path).replace("\\", "/")
    return any(frag in s for frag in ALLOWED_PATH_FRAGMENTS)

def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_no, value, line_text) for offending hexes."""
    findings: list[tuple[int, str, str]] = []
    in_block_comment = False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw
        # naive block-comment tracking
        if in_block_comment:
            end = line.find("*/")
            if end < 0:
                continue
            line = line[end + 2:]
            in_block_comment = False
        while True:
            start = line.find("/*")
            if start < 0:
                break
            end = line.find("*/", start + 2)
            if end < 0:
                line = line[:start]
                in_block_comment = True
                break
            line = line[:start] + line[end + 2:]
        if line.strip().startswith("//"):  # not real CSS but defensive
            continue
        for m in HEX_RE.finditer(line):
            value = m.group(0).lower()
            if value in ALLOWED_VALUES:
                continue
            findings.append((ln, value, raw.strip()))
    return findings

def main(argv: list[str]) -> int:
    # pre-commit passes filenames; if none provided, scan project default dirs.
    if argv:
        paths = [Path(a) for a in argv]
    else:
        base = Path("crkva/registar/static/registar")
        paths = list(base.rglob("*.css"))
    # Only CSS files
    paths = [p for p in paths if p.suffix == ".css"]
    violations: list[tuple[Path, list[tuple[int, str, str]]]] = []
    for p in paths:
        if is_allowed_file(p):
            continue
        findings = scan_file(p)
        if findings:
            violations.append((p, findings))
    if not violations:
        return 0
    print("Hardcoded hex colors found in component CSS (use var(--color-*) tokens):")
    print()
    for path, findings in violations:
        for ln, value, snippet in findings:
            print(f"  {path}:{ln}  {value}")
            print(f"      {snippet}")
    print()
    print("Allowed only in:")
    print("  - crkva/registar/static/registar/base/tokens.css")
    print("  - crkva/registar/static/registar/themes/*.css")
    print("  - crkva/registar/static/registar/print/*.css")
    print(f"  - the values {sorted(ALLOWED_VALUES)} (affordance whites/blacks)")
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
