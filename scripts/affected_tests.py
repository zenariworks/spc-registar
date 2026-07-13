#!/usr/bin/env python3
"""Pre-commit hook: run only the Django tests affected by staged Python changes.

Strategy (strict-scoped):
- Map each staged ``.py`` file to its dotted module.
- Build a first-party import graph over the whole ``crkva`` tree and, for each
  test module, compute the modules it transitively imports (re-exports through
  ``__init__`` included).
- A test module is *affected* if it reaches a changed source module, or if it
  is itself a changed test module.
- Run exactly those test modules. If nothing is affected, run nothing.

What this deliberately does NOT catch: dependencies via dynamic import,
templates, fixtures, signals, or URL wiring — a static scan can't see them.
The full suite runs in CI (.github/workflows/tests.yml) on push/PR as the
safety net for those.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import warnings
from pathlib import Path

# Parsing arbitrary project files raises SyntaxWarning for unescaped regex
# strings; irrelevant to import extraction.
warnings.filterwarnings("ignore", category=SyntaxWarning)

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "crkva"
FIRST_PARTY = ("registar", "tenants", "kalendar", "crkva")


def path_to_module(path: Path) -> str | None:
    """Return the dotted module for a repo path under ``crkva/``, else None."""
    try:
        rel = path.resolve().relative_to(SRC_ROOT)
    except ValueError:
        return None
    if rel.suffix != ".py":
        return None
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts or parts[0] not in FIRST_PARTY:
        return None
    return ".".join(parts)


def module_exists(mod: str) -> bool:
    """True if the dotted module resolves to a file or package under crkva/."""
    base = SRC_ROOT / Path(*mod.split("."))
    return base.with_suffix(".py").exists() or (base / "__init__.py").exists()


def resolve_to_module(name: str) -> str | None:
    """Map an imported name to the nearest existing module (handles
    ``from pkg import symbol`` where ``pkg.symbol`` is not itself a module)."""
    parts = name.split(".")
    while parts:
        cand = ".".join(parts)
        if cand.split(".", maxsplit=1)[0] in FIRST_PARTY and module_exists(cand):
            return cand
        parts.pop()
    return None


def raw_imports(path: Path, mod: str) -> set[str]:
    """Collect the raw imported names (absolute + resolved-relative) in a file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return set()
    pkg = mod.rsplit(".", 1)[0] if "." in mod else mod
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import
                base = pkg.split(".")
                if node.level > 1:
                    base = base[: -(node.level - 1)] or base
                target = ".".join(base + ([node.module] if node.module else []))
            else:
                target = node.module or ""
            if target:
                names.add(target)
                for a in node.names:
                    names.add(f"{target}.{a.name}")
    return names


def build_graph() -> tuple[dict[str, set[str]], list[str]]:
    """Build the first-party import graph and list all test modules."""
    edges: dict[str, set[str]] = {}
    tests: list[str] = []
    for top in FIRST_PARTY:
        for f in (SRC_ROOT / top).rglob("*.py"):
            mod = path_to_module(f)
            if mod is None:
                continue
            deps = {
                m
                for name in raw_imports(f, mod)
                if (m := resolve_to_module(name)) and m != mod
            }
            edges[mod] = deps
            leaf = f.name
            if ".tests." in f"{mod}." or mod.endswith(".tests"):
                if leaf.startswith("test_"):
                    tests.append(mod)
    return edges, tests


def reachable(start: str, edges: dict[str, set[str]]) -> set[str]:
    """Return every module transitively imported from ``start``."""
    seen: set[str] = set()
    stack = [start]
    while stack:
        cur = stack.pop()
        for dep in edges.get(cur, ()):
            if dep not in seen:
                seen.add(dep)
                stack.append(dep)
    return seen


def main(argv: list[str]) -> int:
    """Run the Django test modules affected by the staged files in ``argv``."""
    changed = {m for p in argv if (m := path_to_module(Path(p)))}
    if not changed:
        return 0  # no first-party .py staged

    edges, tests = build_graph()
    changed_tests = {m for m in changed if m in tests}
    changed_sources = changed - changed_tests

    affected = set(changed_tests)
    for t in tests:
        if reachable(t, edges) & changed_sources:
            affected.add(t)

    if not affected:
        print(
            "affected-tests: no test module imports the staged changes; "
            "skipping (full suite runs in CI).",
            file=sys.stderr,
        )
        return 0

    labels = sorted(affected)
    print(f"affected-tests: running {len(labels)} module(s):", file=sys.stderr)
    for lbl in labels:
        print(f"  - {lbl}", file=sys.stderr)

    cmd = [
        sys.executable,
        "crkva/manage.py",
        "test",
        *labels,
        "--keepdb",
        "--parallel",
        "1",
        "--verbosity=1",
    ]
    return subprocess.run(cmd, cwd=REPO_ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
